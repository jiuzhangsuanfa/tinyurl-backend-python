import random
import re
import time
import zlib
import ipaddress
import hashlib

from functools import wraps
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

from .exceptions import Ratelimited

CHAR_SET = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

# Extend the expiration time by a few seconds to avoid misses.
EXPIRATION_FUDGE = 5


def generate_short_key():
    short_key = ""
    for i in range(6):
        random_num = random.randint(0, 61)
        short_key += CHAR_SET[random_num]

    return short_key


def id_2_short_key(fid, alphabet=CHAR_SET):
    if fid == 0:
        return alphabet[0]

    arr = []
    base = len(alphabet)
    while fid:
        fid, rem = divmod(fid, base)
        arr.append(alphabet[rem])
    arr.reverse()

    return ''.join(arr)


def short_key_2_id (short_key):
    digit = 0
    fid = 0
    for i in short_key[::-1]:
        num = CHAR_SET.find(i)
        fid += num * 62 ** digit
        digit += 1

    return fid


# def ratelimiter(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         try:
#             ip_address = args[0].headers['Referer']
#
#             count = cache.get(ip_address)
#             if count is None:
#                 count = 0
#
#             # 5秒最多访问5次
#             if count >= 5:
#                 res = {
#                     "url": "The operation is too frequent, please try again later"
#                 }
#                 response = HttpResponse(json.dumps(res))
#
#                 return response
#             else:
#                 count += 1
#                 cache.set(ip_address, count, timeout=5)
#
#             return func(*args, **kwargs)
#
#         except Exception:
#             return func(*args, **kwargs)
#
#     return wrapper


def ip_mask(ip):
    if ':' in ip:
        # IPv6
        mask = getattr(settings, 'RATELIMIT_IPV6_MASK', 64)
    else:
        # IPv4
        mask = getattr(settings, 'RATELIMIT_IPV4_MASK', 32)

    network = ipaddress.ip_network('{}/{}'.format(ip, mask), strict=False)

    return str(network.network_address)


def _get_window(value, period):
    ts = int(time.time())
    if period == 1:
        return ts
    if not isinstance(value, bytes):
        value = value.encode('utf-8')
    w = ts - (ts % period) + (zlib.crc32(value) % period)
    if w < ts:
        return w + period
    return w


def _make_cache_key(window, rate, value):
    count, period = _split_rate(rate)
    safe_rate = '%d/%ds' % (count, period)
    parts = [safe_rate, value, str(window)]
    prefix = getattr(settings, 'RATELIMIT_CACHE_PREFIX', 'rl:')
    return prefix + hashlib.md5(u''.join(parts).encode('utf-8')).hexdigest()


rate_re = re.compile(r'([\d]+)/([\d]*)([smhd])?')


def _split_rate(rate):
    if isinstance(rate, tuple):
        return rate
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    if not period:
        period = 's'
    seconds = _PERIODS[period.lower()]
    if multi:
        seconds = seconds * int(multi)
    return count, seconds


def is_ratelimited(request, fn=None, rate=None, strategy=None, increment=False):
    usage = get_usage(request, fn, rate, strategy, increment)
    if usage is None:
        return False

    return usage['should_limit']


def get_usage(requset, fn=None, rate=None, strategy=None, increment=False):
    if fn is None:
        raise ImproperlyConfigured('get_usage must be called with `fn` arguments')

    if not getattr(settings, 'RATELIMIT_ENABLE', True):
        return None

    if rate is None:
        return None
    limit, period = _split_rate(rate)
    if period <= 0:
        raise ImproperlyConfigured('Ratelimit period must be greater than 0')

    get_ip = lambda r: ip_mask(r.META['REMOTE_ADDR'])
    value = get_ip(requset)

    window = _get_window(value, period)
    initial_value = 1 if increment else 0

    cache_key = _make_cache_key(window, rate, value)

    count = None
    added = cache.add(cache_key, initial_value, period + EXPIRATION_FUDGE)
    if added:
        count = initial_value
    else:
        if increment:
            try:
                # python3-memcached will throw a ValueError if the server is
                # unavailable or (somehow) the key doesn't exist. redis, on the
                # other hand, simply returns None.
                count = cache.incr(cache_key)
            except ValueError:
                pass
        else:
            count = cache.get(cache_key, initial_value)

    # Getting or setting the count from the cache failed
    if count is None:
        if getattr(settings, 'RATELIMIT_FAIL_OPEN', False):
            return None
        return {
            'count': 0,
            'limit': 0,
            'should_limit': True,
            'time_left': -1,
        }

    time_left = window - int(time.time())
    return {
        'count': count,
        'limit': limit,
        'should_limit': count > limit,
        'time_left': time_left,
    }


def ratelimiter(rate=None, strategy=None, block=False):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            old_limited = getattr(request, 'limited', False)
            ratelimited = is_ratelimited(request=request, fn=fn, rate=rate, strategy=strategy, increment=True)
            request.limited = ratelimited or old_limited
            if ratelimited and block:
                raise Ratelimited()
            return fn(request, *args, **kwargs)

        return _wrapped

    return decorator


if __name__ == "__main__":
    pass



