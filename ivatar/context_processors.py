'''
Default: useful variables for the base page templates.
'''

from ivatar.settings import IVATAR_VERSION, SITE_NAME
from ipware import get_client_ip

def basepage(request):
    context = {}
    if 'openid_identifier' in request.GET:
        context['openid_identifier'] = request.GET['openid_identifier']
    client_ip, is_routable = get_client_ip(request)
    context['client_ip'] = client_ip
    context['ivatar_version'] = IVATAR_VERSION
    context['site_name'] = SITE_NAME
    return context
