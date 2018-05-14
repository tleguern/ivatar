'''
ivatar URL Configuration
'''
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from django.conf.urls.static import static
from ivatar import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    url('openid/', include('django_openid_auth.urls')),
    url('accounts/', include('ivatar.ivataraccount.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
