'''
ivatar/tools URL configuration
'''

from django.conf.urls import url
from . views import CheckView, CheckDomainView

urlpatterns = [  # pylint: disable=invalid-name
    url('check/', CheckView.as_view(), name='tools_check'),
    url('check_domain/', CheckDomainView.as_view(), name='tools_check_domain'),
]
