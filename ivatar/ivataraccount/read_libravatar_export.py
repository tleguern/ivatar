'''
Reading libravatar export
'''

from io import BytesIO
import gzip
import xml.etree.ElementTree
import base64
from PIL import Image

SCHEMAROOT = 'https://www.libravatar.org/schemas/export/0.2'

def read_gzdata(gzdata=None):
    '''
    Read gzipped data file
    '''
    emails = []  # pylint: disable=invalid-name
    openids = []   # pylint: disable=invalid-name
    photos = []   # pylint: disable=invalid-name

    if not gzdata:
        return False

    fh = gzip.open(BytesIO(gzdata), 'rb')  # pylint: disable=invalid-name
    content = fh.read()
    fh.close()
    root = xml.etree.ElementTree.fromstring(content)
    if not root.tag == '{%s}user' % SCHEMAROOT:
        print('Unknown export format: %s' % root.tag)
        exit(-1)

    # Emails
    for email in root.findall('{%s}emails' % SCHEMAROOT)[0]:
        if email.tag == '{%s}email' % SCHEMAROOT:
            emails.append(email.text)

    # OpenIDs
    for openid in root.findall('{%s}openids' % SCHEMAROOT)[0]:
        if openid.tag == '{%s}openid' % SCHEMAROOT:
            openids.append(openid.text)

    # Photos
    for photo in root.findall('{%s}photos' % SCHEMAROOT)[0]:
        if photo.tag == '{%s}photo' % SCHEMAROOT:
            try:
                data = base64.decodebytes(bytes(photo.text, 'utf-8'))
            except Exception as e:  # pylint: disable=broad-except,invalid-name
                print('Cannot decode photo; Encoding: %s, Format: %s: %s' % (
                    photo.attrib['encoding'], photo.attrib['format'], e))
                continue
            try:
                img = Image.open(BytesIO(data))
            except Exception as e:  # pylint: disable=broad-except,invalid-name
                print('Cannot decode photo; Encoding: %s, Format: %s: %s' % (
                    photo.attrib['encoding'], photo.attrib['format'], e))
                continue

            photos.append(img)

    return {
        'emails': emails,
        'openids': openids,
        'photos': photos,
    }
