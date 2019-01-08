#!/usr/bin/env python
'''
Import the whole libravatar export
'''

import os
from os.path import isfile, isdir, join
import sys
import base64
from io import BytesIO
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ivatar.settings")  # pylint: disable=wrong-import-position
django.setup()  # pylint: disable=wrong-import-position
from django.contrib.auth.models import User
from PIL import Image
from django_openid_auth.models import UserOpenID
from ivatar.settings import JPEG_QUALITY
from ivatar.ivataraccount.read_libravatar_export import read_gzdata as libravatar_read_gzdata
from ivatar.ivataraccount.models import ConfirmedEmail
from ivatar.ivataraccount.models import ConfirmedOpenId
from ivatar.ivataraccount.models import Photo
from ivatar.ivataraccount.models import file_format

if len(sys.argv) < 2:
    print("First argument to '%s' must be the path to the exports" % sys.argv[0])
    exit(-255)

if not isdir(sys.argv[1]):
    print("First argument to '%s' must be a directory containing the exports" % sys.argv[0])
    exit(-255)

PATH = sys.argv[1]
for file in os.listdir(PATH):
    if not file.endswith('.xml.gz'):
        continue
    if isfile(join(PATH, file)):
        fh = open(join(PATH, file), 'rb')
        items = libravatar_read_gzdata(fh.read())
        print('Adding user "%s"' % items['username'])
        (user, created) = User.objects.get_or_create(username=items['username'])
        user.password = items['password']
        user.save()

        saved_photos = {}
        for photo in items['photos']:
            photo_id = photo['id']
            data = base64.decodebytes(bytes(photo['data'], 'utf-8'))
            pilobj = Image.open(BytesIO(data))
            out = BytesIO()
            pilobj.save(out, pilobj.format, quality=JPEG_QUALITY)
            out.seek(0)
            photo = Photo()
            photo.user = user
            photo.ip_address = '0.0.0.0'
            photo.format = file_format(pilobj.format)
            photo.data = out.read()
            photo.save()
            saved_photos[photo_id] = photo

        for email in items['emails']:
            try:
                ConfirmedEmail.objects.get_or_create(email=email['email'], user=user,
                                                     photo=saved_photos.get(email['photo_id']))
            except django.db.utils.IntegrityError:
                print('%s not unique?' % email['email'])

        for openid in items['openids']:
            try:
                ConfirmedOpenId.objects.get_or_create(openid=openid['openid'], user=user,
                                                      photo=saved_photos.get(openid['photo_id'])) # pylint: disable=no-member
                UserOpenID.objects.get_or_create(
                    user_id=user.id,
                    claimed_id=openid['openid'],
                    display_id=openid['openid'],
                )
            except django.db.utils.IntegrityError:
                print('%s not unique?' % openid['openid'])

        fh.close()
