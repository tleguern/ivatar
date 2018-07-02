'''
ivatar URL configuration
'''
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from django.conf.urls.static import static
from django.views.generic import TemplateView
from ivatar import settings
from . views import AvatarImageView

urlpatterns = [  # pylint: disable=invalid-name
    path('admin/', admin.site.urls),
    url('openid/', include('django_openid_auth.urls')),
    url('accounts/', include('ivatar.ivataraccount.urls')),
    url('tools/', include('ivatar.tools.urls')),
    url(
        r'avatar/(?P<digest>\w{64})',
        AvatarImageView.as_view(), name='avatar_view'),
    url(
        r'avatar/(?P<digest>\w{32})',
        AvatarImageView.as_view(), name='avatar_view'),
    url('', TemplateView.as_view(template_name='home.html')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
