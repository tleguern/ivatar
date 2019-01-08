'''
Helper method to fetch Gravatar image
'''
from ssl import SSLError
from urllib.request import urlopen, HTTPError, URLError
import hashlib

from .. settings import AVATAR_MAX_SIZE

URL_TIMEOUT = 5  # in seconds


def get_photo(email):
    '''
    Fetch photo from Gravatar, given an email address
    '''
    hash_object = hashlib.new('md5')
    hash_object.update(email.lower().encode('utf-8'))
    thumbnail_url = 'https://secure.gravatar.com/avatar/' + \
        hash_object.hexdigest() + '?s=%i&d=404' % AVATAR_MAX_SIZE
    image_url = 'https://secure.gravatar.com/avatar/' + hash_object.hexdigest(
        ) + '?s=512&d=404'

    # Will redirect to the public profile URL if it exists
    service_url = 'http://www.gravatar.com/' + hash_object.hexdigest()

    try:
        urlopen(image_url, timeout=URL_TIMEOUT)
    except HTTPError as exc:
        if exc.code != 404 and exc.code != 503:
            print(  # pragma: no cover
                'Gravatar fetch failed with an unexpected %s HTTP error' %
                exc.code)
        return False
    except URLError as exc:  # pragma: no cover
        print(
            'Gravatar fetch failed with URL error: %s' %
            exc.reason)  # pragma: no cover
        return False  # pragma: no cover
    except SSLError as exc:   # pragma: no cover
        print(
            'Gravatar fetch failed with SSL error: %s' %
            exc.reason)  # pragma: no cover
        return False  # pragma: no cover

    return {
        'thumbnail_url': thumbnail_url,
        'image_url': image_url,
        'width': AVATAR_MAX_SIZE,
        'height': AVATAR_MAX_SIZE,
        'service_url': service_url,
        'service_name': 'Gravatar'
    }
