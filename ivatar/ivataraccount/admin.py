'''
Register models in admin
'''
from django.contrib import admin

from . models import Photo, ConfirmedEmail, UnconfirmedEmail
from . models import ConfirmedOpenId, UnconfirmedOpenId
from . models import OpenIDNonce, OpenIDAssociation
from . models import UserPreference

# Register models in admin
admin.site.register(Photo)
admin.site.register(ConfirmedEmail)
admin.site.register(UnconfirmedEmail)
admin.site.register(ConfirmedOpenId)
admin.site.register(UnconfirmedOpenId)
admin.site.register(UserPreference)
admin.site.register(OpenIDNonce)
admin.site.register(OpenIDAssociation)
