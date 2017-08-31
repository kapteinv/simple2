# from unittest.mock import MagicMock
from django.test import TestCase
# from django.core.files import File
from django.contrib.auth.models import User
from account.models import Account
from gnupg import GPG

# file_mock = MagicMock(spec=File, name='FileMock')
# file_mock.name = "avatarimg.jpg"


class AccountModelTest(TestCase):

    def test_create_and_retrieving_users_and_their_account(self):
        user01 = User.objects.create(username="user01")
        user02 = User.objects.create(username="user02")

        account01 = Account(
            user=user01, fdw_identity="user01", fdw_id=1
        )
        account01.save()

        account02 = Account(
            user=user02, fdw_identity="user02", fdw_id=2
        )
        account02.save()

        first_saved_account = Account.objects.first()
        self.assertEqual(first_saved_account, account01)

        saved_accounts = Account.objects.all()
        self.assertEqual(saved_accounts.count(), 2)

        second_saved_account = saved_accounts[1]
        self.assertEqual(first_saved_account.user, user01)
        self.assertEqual(first_saved_account.fdw_id, 1)
        self.assertEqual(second_saved_account.user, user02)
        self.assertEqual(second_saved_account.fdw_id, 2)

    def test_get_absolute_url(self):
        user_ = User.objects.create(username="azerty")
        account_ = Account.objects.create(user=user_)
        self.assertEqual(
            account_.get_absolute_url(), '/account/{}/'.format(account_.slug,)
            )

    def test_gpg(self):
        gpg = GPG("gpg1")
        gpg.encoding = 'utf-8'
        input_data = gpg.gen_key_input(key_type="RSA", key_length=1024)
        key = gpg.gen_key(input_data)
        ascii_armored_public_key = gpg.export_keys(key.fingerprint)
        user_ = User.objects.create(username="gpguser")
        account_ = Account.objects.create(
            user=user_,
            gpg=ascii_armored_public_key
        )
        self.assertEqual(account_.fingerprint, key.fingerprint)
