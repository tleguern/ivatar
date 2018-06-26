'''
Simple module providing reusable random_string function
'''
import random
import string


def random_string(length=10):
    '''
    Return some random string with default length 10
    '''
    return ''.join(random.SystemRandom().choice(
        string.ascii_lowercase + string.digits) for _ in range(length))
