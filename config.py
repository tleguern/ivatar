import os
from sys import platform, argv
from ivatar.settings import BASE_DIR

if os.path.isfile(os.path.join(BASE_DIR, 'config_local.py')):
    from config_local import *  # noqa # flake8: noqa # NOQA # pragma: no cover

ADMIN_USERS = []
ALLOWED_HOSTS = [
    'localhost',
]

from ivatar.settings import INSTALLED_APPS # noqa
INSTALLED_APPS.extend([
    'django_extensions',
    'django_openid_auth',
    'bootstrap4',
    'ivatar',
    'ivatar.ivataraccount',
])

from ivatar.settings import MIDDLEWARE  # noqa
MIDDLEWARE.extend([
    'django.middleware.locale.LocaleMiddleware',
])

AUTHENTICATION_BACKENDS = (
    # Enable this to allow LDAP authentication. See INSTALL for more information.
    # 'django_auth_ldap.backend.LDAPBackend',
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

from ivatar.settings import TEMPLATES
TEMPLATES[0]['DIRS'].extend([
    os.path.join(BASE_DIR, 'templates'),
])
TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'ivatar.context_processors.basepage',
)

OPENID_CREATE_USERS = True
OPENID_UPDATE_DETAILS_FROM_SREG = True

IVATAR_VERSION = '0.1'

LOGIN_REDIRECT_URL = '/account/profile/'
