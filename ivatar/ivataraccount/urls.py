'''
URLs for ivatar.ivataraccount
'''
from django.urls import path
from django.conf.urls import url

from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required

from . views import CreateView, PasswordSetView, AddEmailView
from . views import RemoveUnconfirmedEmailView, ConfirmEmailView
from . views import RemoveConfirmedEmailView, AssignPhotoEmailView
from . views import RemoveUnconfirmedOpenIDView, RemoveConfirmedOpenIDView
from . views import ImportPhotoView, RawImageView, DeletePhotoView
from . views import UploadPhotoView, AssignPhotoOpenIDView
from . views import AddOpenIDView, RedirectOpenIDView, ConfirmOpenIDView
from . views import CropPhotoView
from . views import UserPreferenceView, UploadLibravatarExportView
from . views import ResendConfirmationMailView

# Define URL patterns, self documenting
# To see the fancy, colorful evaluation of these use:
# ./manager show_urls
urlpatterns = [  # pylint: disable=invalid-name
    path('new/', CreateView.as_view(), name='new_account'),
    path('login/', LoginView.as_view(template_name='login.html'),
         name='login'),
    path(
        'logout/', LogoutView.as_view(next_page='/'),
        name='logout'),
    path('export/', login_required(
        TemplateView.as_view(template_name='export.html')
    ), name='export'),
    path('delete/', login_required(
        TemplateView.as_view(template_name='delete.html')
    ), name='delete'),
    path('profile/', login_required(
        TemplateView.as_view(template_name='profile.html')
    ), name='profile'),
    path('add_email/', AddEmailView.as_view(), name='add_email'),
    path('add_openid/', AddOpenIDView.as_view(), name='add_openid'),
    path('upload_photo/', UploadPhotoView.as_view(), name='upload_photo'),
    path('password_set/', PasswordSetView.as_view(), name='password_set'),
    url(
        r'remove_unconfirmed_openid/(?P<openid_id>\d+)',
        RemoveUnconfirmedOpenIDView.as_view(),
        name='remove_unconfirmed_openid'),
    url(
        r'remove_confirmed_openid/(?P<openid_id>\d+)',
        RemoveConfirmedOpenIDView.as_view(), name='remove_confirmed_openid'),
    url(
        r'openid_redirection/(?P<openid_id>\d+)',
        RedirectOpenIDView.as_view(), name='openid_redirection'),
    url(
        r'confirm_openid/(?P<openid_id>\w+)',
        ConfirmOpenIDView.as_view(), name='confirm_openid'),
    url(
        r'confirm_email/(?P<verification_key>\w+)',
        ConfirmEmailView.as_view(), name='confirm_email'),
    url(
        r'remove_unconfirmed_email/(?P<email_id>\d+)',
        RemoveUnconfirmedEmailView.as_view(), name='remove_unconfirmed_email'),
    url(
        r'remove_confirmed_email/(?P<email_id>\d+)',
        RemoveConfirmedEmailView.as_view(), name='remove_confirmed_email'),
    url(
        r'assign_photo_email/(?P<email_id>\d+)',
        AssignPhotoEmailView.as_view(), name='assign_photo_email'),
    url(
        r'assign_photo_openid/(?P<openid_id>\d+)',
        AssignPhotoOpenIDView.as_view(), name='assign_photo_openid'),
    url(
        r'import_photo/$',
        ImportPhotoView.as_view(), name='import_photo'),
    url(
        r'import_photo/(?P<email_addr>[\w.]+@[\w.]+.[\w.]+)',
        ImportPhotoView.as_view(), name='import_photo'),
    url(
        r'import_photo/(?P<email_id>\d+)',
        ImportPhotoView.as_view(), name='import_photo'),
    url(
        r'delete_photo/(?P<pk>\d+)',
        DeletePhotoView.as_view(), name='delete_photo'),
    url(r'raw_image/(?P<pk>\d+)', RawImageView.as_view(), name='raw_image'),
    url(r'crop_photo/(?P<pk>\d+)', CropPhotoView.as_view(), name='crop_photo'),
    url(r'pref/$', UserPreferenceView.as_view(), name='user_preference'),
    url(r'upload_export/$', UploadLibravatarExportView.as_view(), name='upload_export'),
    url(r'upload_export/(?P<save>save)$',
        UploadLibravatarExportView.as_view(), name='upload_export'),
    url(r'resend_confirmation_mail/(?P<email_id>\d+)',
        ResendConfirmationMailView.as_view(), name='resend_confirmation_mail'),
]
