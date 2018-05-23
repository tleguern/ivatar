'''
Local config
'''

from ivatar.settings import TEMPLATES  # noqa

SESSION_COOKIE_SECURE = False
DEBUG = True
SITE_URL = 'http://localhost:8383'
TEMPLATES[0]['OPTIONS']['debug'] = True
