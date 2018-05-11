from ssl import SSLError
from urllib.request import urlopen, HTTPError, URLError
import hashlib

URL_TIMEOUT = 5  # in seconds

def get_photo(email):
    '''
    Fetch photo from Gravatar, given an email address
    '''
    hash_object = hashlib.new('md5')                                                                                                           
    hash_object.update(email.lower().encode('utf-8'))
    thumbnail_url = 'https://secure.gravatar.com/avatar/' + hash_object.hexdigest(
        ) + '?s=80&d=404'
    image_url = 'https://secure.gravatar.com/avatar/' + hash_object.hexdigest(
        ) + '?s=512&d=404'

    # Will redirect to the public profile URL if it exists
    service_url = 'http://www.gravatar.com/' + hash_object.hexdigest()

    try:
        urlopen(image_url, timeout=URL_TIMEOUT)
    except HTTPError as e:
        if e.code != 404 and e.code != 503:
            print('Gravatar fetch failed with an unexpected %s HTTP error' %  # pragma: no cover
                  e.code)
        return False
    except URLError as e: # pragma: no cover
        print('Gravatar fetch failed with URL error: %s' % e.reason)  # pragma: no cover
        return False  # pragma: no cover
    except SSLError as e:   # pragma: no cover
        print('Gravatar fetch failed with SSL error: %s' % e.reason)  # pragma: no cover
        return False  # pragma: no cover

    return {
        'thumbnail_url': thumbnail_url,
        'image_url': image_url,
        'width': 80,
        'height': 80,
        'service_url': service_url,
        'service_name': 'Gravatar'
    }
