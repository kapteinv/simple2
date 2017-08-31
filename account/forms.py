import hashlib

from django.forms import CharField, PasswordInput, Textarea, EmailField
from django.forms import RegexField, ModelForm, EmailInput, Form
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from gnupg import GPG

from .models import Account
from . import queryfdw


class CreateUserForm(ModelForm):
    # http://effectivedjango.com/tutorial/forms.html
    # https://docs.djangoproject.com/fr/1.7/_modules/django/contrib/auth/forms/
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
        'fdw_check_fail': _(
            "Cannot verify your FDW identity,"
            " if you think you have provided the correct credentials,"
            " please contact a modo or an admin"
        ),
        'none_fdw_passwd': _(
            "FDW identity and FDW password fields can not be empty "
        ),
        'banned_fdw_identity': _(
            "Your fdw_identity is linked to a banned user, you are not welcome"
        )
    }
    username = RegexField(
        label=_("Username"), max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=_("Required. 30 characters or fewer. Letters, digits and "
                    "@/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")
        }
    )
    password1 = CharField(
        label=_("Password"),
        widget=PasswordInput
    )
    password2 = CharField(
        label=_("Password confirmation"),
        widget=PasswordInput,
        help_text=_("Enter the same password as above, for verification.")
    )
    fdw_identity = CharField(label=_("FDW Identity"))
    fdw_password_raw = CharField(
        label=_("FDW Password"),
        widget=PasswordInput,
        help_text=_("Enter Your FDW password")
    )
    email = EmailField(
        label=_("Email address"),
        widget=EmailInput,
        required=False
    )
    gpg = CharField(label="Pubkey", required=False, widget=Textarea())

    def clean(self):
        is_clean = super(CreateUserForm, self).clean()
        fdw_identity = self.cleaned_data.get("fdw_identity")
        fdw_password_raw = self.cleaned_data.get("fdw_password_raw")
        banneds = User.objects.filter(account__banned=True)
        try:
            fdw_password = (
                hashlib.sha1(fdw_password_raw.encode('utf-8')).hexdigest()
            )
        except AttributeError:
            raise ValidationError(
                self.error_messages['none_fdw_passwd'],
                code='none_fdw_passwd',
            )
        check_fdw = queryfdw.QueryFDW(fdw_identity)
        # assignment to fdw_query
        fdw_identitysql = check_fdw.identity()[0]
        fdw_passwordsql = check_fdw.identity()[1]

        # test identity
        if fdw_identity.upper() != fdw_identitysql.upper():
            raise ValidationError(
                self.error_messages['fdw_check_fail'],
                code='fdw_check_fail',
            )
        # test banned
        for user in banneds:
            if fdw_identity == user.account.fdw_identity:
                raise ValidationError(
                    self.error_messages['banned_fdw_identity'],
                    code='banned_fdw_identity',
                )

        # test password
        if fdw_password != fdw_passwordsql:
            raise ValidationError(
                self.error_messages['fdw_check_fail'],
                code='fdw_check_fail',
            )

        return is_clean

    class Meta:
        model = User
        fields = ("username",)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"]),
        if commit:
            user.save()
            check_fdw = queryfdw.QueryFDW(self.cleaned_data["fdw_identity"])
            fdw_id = check_fdw.identity()[2]
            Account.objects.create(
                user=user,
                fdw_identity=self.cleaned_data["fdw_identity"],
                fdw_id=fdw_id,
                email=(
                    self.cleaned_data["email"]
                ),
                jid=(
                    self.cleaned_data["username"] +
                    "@fdw.libertygb2nyeyay.onion"
                ),
                gpg=self.cleaned_data["gpg"]
            )

        return user


class VerifyVendorForm(Form):
    """
    A form that verify the signed message is signed with the user openPGP key
    and give vendor rights to the user
    """
    error_messages = {
        'sig_not_verified': _("Signature could not be verified!"),
        'key_error': _("Your openPGP key is not valid!"),
        'sig_not_by_user': _("Signature not match your account openPGP key!")
    }
    signed_msg = CharField(
        label="signed_msg",
        required=True, widget=Textarea()
        )

    def __init__(self, *args, **kwargs):
        # To get request.user. Do not use kwargs.pop('user', None)
        # due to potential security hole
        self.user = kwargs.pop('user')

        super(VerifyVendorForm, self).__init__(*args, **kwargs)

    def clean(self):
        gpg = GPG()
        gpg.encoding = 'utf-8'
        is_clean = super(VerifyVendorForm, self).clean()
        signed_msg = self.cleaned_data.get("signed_msg")
        verified = gpg.verify(signed_msg)
        key = gpg.import_keys(self.user.account.gpg)

        if not verified:
            raise ValidationError(
                self.error_messages['sig_not_verified'],
                code='sig_not_verified'
            )

        if key.count == 0:
            raise ValidationError(
                self.error_messages['key_error'],
                code='key_error'
            )

        if verified.pubkey_fingerprint != key.fingerprints[0]:
            raise ValidationError(
                self.error_messages['sig_not_by_user'],
                code='sig_not_by_user'
            )

        if verified.pubkey_fingerprint == key.fingerprints[0]:
            user = self.user
            group = Group.objects.get(name='vendor')
            user.groups.add(group)

        return is_clean
