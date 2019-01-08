#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2018 Oliver Falk <oliver@linux-kernel.at>
#
# This file is part of Libravatar
#
# Libravatar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Libravatar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Libravatar.  If not, see <http://www.gnu.org/licenses/>.

import base64
import gzip
import json
import os
import sys
from xml.sax import saxutils
import hashlib

# pylint: disable=relative-import
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "libravatar.settings")
import libravatar.settings as settings
from libravatar.utils import create_logger, is_hex
import django
django.setup()
from django.contrib.auth.models import User

os.umask(022)
LOGGER = create_logger('exportaccount')

SCHEMA_ROOT = 'https://www.libravatar.org/schemas/export/0.2'
SCHEMA_XSD = '%s/export.xsd' % SCHEMA_ROOT


def xml_header():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<user xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="%s %s"
      xmlns="%s">\n''' % (SCHEMA_ROOT, SCHEMA_XSD, SCHEMA_ROOT)


def xml_footer():
    return '</user>\n'


def xml_account(username, password):
    escaped_username = saxutils.quoteattr(username)
    escaped_site_url = saxutils.quoteattr(settings.SITE_URL)
    escaped_password = saxutils.quoteattr(password)
    return '  <account username=%s password=%s site=%s/>\n' % (escaped_username, escaped_password, escaped_site_url)

def xml_email(emails):
    returnstring = "  <emails>\n"
    for email in emails:
        returnstring += '    <email photo_id="' + str(email.photo_id) + '">' + email.email.encode('utf-8') + '</email>' + "\n"
    returnstring += "  </emails>\n"
    return returnstring

def xml_openid(openids):
    returnstring = "  <openids>\n"
    for openid in openids:
        returnstring += '    <openid photo_id="' + str(openid.photo_id) + '">' + openid.openid.encode('utf-8') + '</openid>' + "\n"
    returnstring += "  </openids>\n"
    return returnstring


def xml_photos(photos):
    s = '  <photos>\n'
    for photo in photos:
        (photo_filename, photo_format, id) = photo
        encoded_photo = encode_photo(photo_filename, photo_format)
        if encoded_photo:
            s += '''    <photo id="%s" encoding="base64" format=%s>
%s
    </photo>\n''' % (id, saxutils.quoteattr(photo_format), encoded_photo)
    s += '  </photos>\n'
    return s


def encode_photo(photo_filename, photo_format):
    filename = settings.USER_FILES_ROOT + photo_filename + '.' + photo_format
    if not os.path.isfile(filename):
        LOGGER.warning('Photo not found: %s', filename)
        return None

    photo_content = None
    with open(filename) as photo:
        photo_content = photo.read()

    if not photo_content:
        LOGGER.warning('Could not read photo: %s', filename)
        return None

    return base64.b64encode(photo_content)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if(len(sys.argv) > 1):
        userobjs = User.objects.filter(username=sys.argv[1])
    else:
        userobjs = User.objects.all()

    for user in userobjs:
        hash_object = hashlib.new('sha256')
        hash_object.update(user.username + user.password)
        file_hash = hash_object.hexdigest()
        photos = []
        for photo in user.photos.all():
            photo_details = (photo.filename, photo.format, photo.id)
            photos.append(photo_details)
        username = user.username
        
        dest_filename = settings.EXPORT_FILES_ROOT + file_hash + '.xml.gz'

        destination = gzip.open(dest_filename, 'w')
        destination.write(xml_header())
        destination.write(xml_account(username, user.password))
        destination.write(xml_email(user.confirmed_emails.all()))
        destination.write(xml_openid(user.confirmed_openids.all()))
        destination.write(xml_photos(photos))
        destination.write(xml_footer())
        destination.close()
        print(dest_filename)
    return 0


if __name__ == "__main__":
    sys.exit(main())
