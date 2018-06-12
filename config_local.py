'''
Local config
'''

from ivatar.settings import TEMPLATES  # noqa

SESSION_COOKIE_SECURE = False
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True
