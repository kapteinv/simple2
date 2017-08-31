# -*- coding: utf-8 -*-
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.views.generic import UpdateView, FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist

from account.forms import CreateUserForm, VerifyVendorForm
from account.models import Account


class ProfileDetailView(DetailView):

    model = Account
    template_name = 'account/profile-detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileDetailView, self).dispatch(*args, **kwargs)


class ProfileUpdate(UpdateView):
    model = Account
    fields = [
        'absence', 'affich_ligne', 'avatar', 'email', 'jid', 'irc', 'ricochet',
        'bitmessage', 'btc', 'description', 'gpg'
    ]
    template_name = 'account/modify_profile.html'

    def get_context_data(self, **kwargs):
        try:
            self.request.user.groups.get(name="escrow")
            self.fields.append('escrow_msg')
        except ObjectDoesNotExist:
            pass
        context = super(ProfileUpdate, self).get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse_lazy(
            'profile',
            kwargs={'slug': self.request.user.account.slug, }
             )

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileUpdate, self).dispatch(*args, **kwargs)


class EscrowList(ListView):
    User.objects.filter(groups__name='escrow')
    model = User
    template_name = "account/escrow_list.html"

    def get_context_data(self, **kwargs):
        context = super(EscrowList, self).get_context_data(**kwargs)
        context['group'] = Group.objects.order_by('name')
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EscrowList, self).dispatch(*args, **kwargs)


class SignupInfoView(TemplateView):
    template_name = "account/signup_info.html"


class SignUpView(CreateView):

    form_class = CreateUserForm
    template_name = 'account/sign_up.html'

    def get_success_url(self):
        return '/login/'


class VerifyVendorView(FormView):

    form_class = VerifyVendorForm
    template_name = 'account/verify_vendor.html'

    def get_form_kwargs(self):
        kwargs = super(VerifyVendorView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            'profile',
            kwargs={'slug': self.request.user.account.slug, }
            )

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(VerifyVendorView, self).dispatch(*args, **kwargs)


class PasswordChangeDoneView(TemplateView):
    template_name = "account/password_change_done.html"
