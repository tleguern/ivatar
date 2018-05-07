from django.urls import path

from django.views.generic import TemplateView
from . views import CreateView, PasswordSetView
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.urls import reverse_lazy

urlpatterns = [
    path('new/', CreateView.as_view(), name='new_account'),
    path('login/', login, { 'template_name': 'login.html' }, name='login'),
    path('logout/', logout, { 'next_page': reverse_lazy('login') }, name='logout'),
    path('export/', TemplateView.as_view(template_name='export.html'), name='export'),
    path('delete/', TemplateView.as_view(template_name='delete.html'), name='delete'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('add_email/', TemplateView.as_view(template_name='add_email.html'), name='add_email'),
    path('add_openid/', TemplateView.as_view(template_name='add_openid.html'), name='add_openid'),
    path('upload_photo/', TemplateView.as_view(template_name='upload_photo.html'), name='upload_photo'),
    path('password_set/', PasswordSetView.as_view(), name='password_set'),
]
