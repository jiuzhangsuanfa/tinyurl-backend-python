import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

from .my_func import ratelimiter
from .tinyurl_service import long_2_short_service, short_2_long_service, long_2_short_v2_service, \
    short_2_long_v2_service


def index(request):
    return render(request, 'conversion/index.html')


@ratelimiter(rate='10/m', block=True)
def long_2_short(request):
    long_url = json.loads(request.body)['url']
    ip_address = request.headers['Referer']

    response = long_2_short_service(long_url, ip_address)

    return HttpResponse(response)


@ratelimiter(rate='60/m', block=True)
def short_2_long(request, short_key):
    long_url = short_2_long_service(short_key)

    return HttpResponseRedirect(long_url)


@ratelimiter(rate='10/m', block=True)
def long_2_short_v2(request):
    long_url = json.loads(request.body)['url']
    ip_address = request.headers['Referer']

    response = long_2_short_v2_service(long_url, ip_address)

    return response


@ratelimiter(rate='60/m', block=True)
def short_2_long_v2(request, short_key):
    long_url = short_2_long_v2_service(short_key)

    return HttpResponseRedirect(long_url)

    """
        1.随机 + base62 + django_views
        2.cache
        3.优化代码，django rest framework + TinyURLService
        4 ratelimiter + Memcached 
        5.MySQL Sharding
            a.settings
            b.Model API 调用不同的数据库
        6.Cassandra 代替 MySQL
    """
