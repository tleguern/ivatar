from django.urls import path
from django.conf.urls import url

from django.views.generic import TemplateView
from . views import CreateView, PasswordSetView, AddEmailView
from . views import RemoveUnconfirmedEmailView, ConfirmEmailView
from . views import RemoveConfirmedEmailView, AssignPhotoEmailView
from . views import ImportPhotoView, RawImageView, DeletePhotoView, UploadPhotoView
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_required

# Define URL patterns, self documenting
# To see the fancy, colorful evaluation of these use:
# ./manager show_urls
urlpatterns = [
    path('new/', CreateView.as_view(), name='new_account'),
    path('login/', login, { 'template_name': 'login.html' }, name='login'),
    path('logout/', logout, { 'next_page': reverse_lazy('login') }, name='logout'),
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
    path('add_openid/', login_required(
        TemplateView.as_view(template_name='add_openid.html')
    ), name='add_openid'),
    path('upload_photo/', UploadPhotoView.as_view(), name='upload_photo'),
    path('password_set/', PasswordSetView.as_view(), name='password_set'),
    url('confirm_email/(?P<verification_key>\w+)', ConfirmEmailView.as_view(), name='confirm_email'),
    url('remove_unconfirmed_email/(?P<email_id>\d+)', RemoveUnconfirmedEmailView.as_view(), name='remove_unconfirmed_email'),
    url('remove_confirmed_email/(?P<email_id>\d+)', RemoveConfirmedEmailView.as_view(), name='remove_confirmed_email'),
    url('assign_photo_email/(?P<email_id>\d+)', AssignPhotoEmailView.as_view(), name='assign_photo_email'),
    url('import_photo/(?P<email_id>\d+)', ImportPhotoView.as_view(), name='import_photo'),
    url('delete_photo/(?P<pk>\d+)', DeletePhotoView.as_view(), name='delete_photo'),
    url('raw_image/(?P<pk>\d+)', RawImageView.as_view(), name='raw_image'),
]
