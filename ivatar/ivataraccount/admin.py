from django.contrib import admin

from . models import Photo, ConfirmedEmail, UnconfirmedEmail
from . models import ConfirmedOpenId, OpenIDNonce, OpenIDAssociation

# Register models in admin
admin.site.register(Photo)
admin.site.register(ConfirmedEmail)
admin.site.register(UnconfirmedEmail)
admin.site.register(ConfirmedOpenId)
admin.site.register(OpenIDNonce)
admin.site.register(OpenIDAssociation)
