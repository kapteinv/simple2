from django.conf.urls import url

from .views import ProfileDetailView, ProfileUpdate, VerifyVendorView

urlpatterns = [
    url(
        r'^modify/(?P<slug>[-_\w]+)/$',
        ProfileUpdate.as_view(),
        name="profileupdate"
        ),
    url(r'^(?P<slug>[-_\w]+)/$', ProfileDetailView.as_view(), name='profile'),
    url(r'^verify/vendor/$', VerifyVendorView.as_view(), name='verifyvendor'),
]
