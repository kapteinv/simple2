from copy import deepcopy

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Account


# Define  an inline admin descriptor for Account model
# witch acts a bit like a singleton
class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False
    verbose_name = 'profile'


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (AccountInline, )
    list_display = (
        'username', 'last_login', 'profile_fdw_identity', 'is_staff',
        'is_active', 'profile_banned', 'profile_inactive'
    )
    list_filter = ('last_login', 'account__banned', 'account__inactive')


    def profile_jid(self, obj):
        return obj.account.jid
    profile_jid.short_description = 'JID(jabber/xmpp ID)'

    def profile_fdw_identity(self, obj):
        return obj.account.fdw_identity
    profile_fdw_identity.short_description = 'FDW identity'

    def profile_banned(self, obj):
        return obj.account.banned
    profile_banned.short_description = 'Bannis'

    def profile_inactive(self, obj):
        return obj.account.inactive
    profile_inactive.short_description = 'Compte inactif'

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(UserAdmin, self).get_fieldsets(request, obj)
        if not obj:
            return fieldsets

        if not request.user.is_superuser or request.user.pk == obj.pk:
            fieldsets = deepcopy(fieldsets)
            for fieldset in fieldsets:
                if 'is_superuser' in fieldset[1]['fields']:
                    if type(fieldset[1]['fields']) == tuple:
                        fieldset[1]['fields'] = list(fieldset[1]['fields'])
                    fieldset[1]['fields'].remove('is_superuser')
                    fieldset[1]['fields'].remove('is_staff')
                    break

        return fieldsets


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
