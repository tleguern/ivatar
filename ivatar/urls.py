'''
ivatar URL configuration
'''
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from ivatar import settings
from . views import AvatarImageView, GravatarProxyView

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
    url(
        r'avatar/(?P<digest>\w*)',
        TemplateView.as_view(
            template_name='error.html',
            extra_context={
                'errormessage': 'Incorrect digest length',
            })),
    url(
        r'gravatarproxy/(?P<digest>\w*)',
        GravatarProxyView.as_view(), name='gravatarproxy'),
    url('description/', TemplateView.as_view(template_name='description.html'), name='description'),
    # The following two are TODO TODO TODO TODO TODO
    url('run_your_own/', TemplateView.as_view(template_name='run_your_own.html'), name='run_your_own'),
    url('features/', TemplateView.as_view(template_name='features.html'), name='features'),
    url('security/', TemplateView.as_view(template_name='security.html'), name='security'),
    url('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('talk_to_us/', RedirectView.as_view(url='/contact'), name='talk_to_us'),
    url('', TemplateView.as_view(template_name='home.html'), name='home'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
