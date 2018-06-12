'''
Configuration overrides for settings.py
'''

import os
from socket import gethostname, gethostbyname
from django.urls import reverse_lazy
from ivatar.settings import BASE_DIR

ADMIN_USERS = []
ALLOWED_HOSTS = [
    'localhost',
    gethostname(),
    gethostbyname(gethostname()),
    '.openshiftapps.com',
    '127.0.0.1',
]

from ivatar.settings import INSTALLED_APPS  # noqa
INSTALLED_APPS.extend([
    'django_extensions',
    'django_openid_auth',
    'bootstrap4',
    'anymail',
    'ivatar',
    'ivatar.ivataraccount',
])

from ivatar.settings import MIDDLEWARE  # noqa
MIDDLEWARE.extend([
    'django.middleware.locale.LocaleMiddleware',
])

AUTHENTICATION_BACKENDS = (
    # Enable this to allow LDAP authentication.
    # See INSTALL for more information.
    # 'django_auth_ldap.backend.LDAPBackend',
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

from ivatar.settings import TEMPLATES  # noqa
TEMPLATES[0]['DIRS'].extend([
    os.path.join(BASE_DIR, 'templates'),
])
TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'ivatar.context_processors.basepage',
)

OPENID_CREATE_USERS = True
OPENID_UPDATE_DETAILS_FROM_SREG = True

SITE_URL = 'https://ivatar.io'
SITE_NAME = 'ivatar'
IVATAR_VERSION = '0.1'

LOGIN_REDIRECT_URL = reverse_lazy('profile')
MAX_LENGTH_EMAIL = 254  # http://stackoverflow.com/questions/386294
SERVER_EMAIL = 'accounts@ivatar.io'
DEFAULT_FROM_EMAIL = SERVER_EMAIL

MAX_NUM_PHOTOS = 5
MAX_PHOTO_SIZE = 10485760  # in bytes

BOOTSTRAP4 = {
    'include_jquery': False,
    'javascript_in_head': False,
    'css_url': {
        'href': '/static/css/bootstrap.min.css',
        'integrity': 'sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB',  # noqa
        'crossorigin': 'anonymous',
    },
    'javascript_url': {
        'url': '/static/js/bootstrap.min.js',
        'integrity': '',
        'crossorigin': 'anonymous',
    },
    'popper_url': {
        'url': '/static/js/popper.min.js',
        'integrity': 'sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49',  # noqa
        'crossorigin': 'anonymous',
    },
}

ANYMAIL = {
    'MAILGUN_API_KEY': '9ea63b269bf14734e928f7aa99f7b891-47317c98-19591231',
    'MAILGUN_SENDER_DOMAIN': 'sandbox86e598eae2de47bcac3926e6d24d789a.mailgun.org',
}
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
DEFAULT_FROM_EMAIL = 'ivatar@linux-kernel.at'

try:
    from ivatar.settings import DATABASES
except Exception:  # pragma: no cover
    DATABASES = []  # pragma: no cover
if not 'default' in DATABASES:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }

#if 'MYSQL_DATABASE' in os.environ:
#    DATABASES['default'] = {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': os.environ['MYSQL_DATABASE'],
#        'USER': os.environ['MYSQL_USER'],
#        'PASSWORD': os.environ['MYSQL_PASSWORD'],
#        'HOST': 'mysql',
#    }

if os.path.isfile(os.path.join(BASE_DIR, 'config_local.py')):
    from config_local import *  # noqa # flake8: noqa # NOQA # pragma: no cover
