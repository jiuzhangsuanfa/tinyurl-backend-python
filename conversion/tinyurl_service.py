import json

from django.utils import timezone
from django.core.cache import cache

from .models import Long2Short, Long2ShortV2
from .my_func import generate_short_key, id_2_short_key, short_key_2_id
from tinyurl.settings import DOMAIN


def long_2_short_service(long_url, ip_address):
    # 查询缓存，如果 short_url 存在，则返回 short_url
    short_url = cache.get(long_url)
    if short_url:
        res = {
            "url": short_url
        }
        return json.dumps(res)

    # 如果 short_url 不存在，则生成一个新的 short_key
    short_key = generate_short_key()
    while Long2Short.objects.filter(short_key=short_key):
        short_key = generate_short_key()

    # 保存数据到数据库
    instance = Long2Short(
        long_url=long_url,
        short_key=short_key,
        created_at=timezone.now(),
        ip_address=ip_address,
    )
    instance.save()

    # 更新缓存
    short_url = DOMAIN + short_key
    cache.set(long_url, short_url, timeout=60 * 60 * 24)
    cache.set(short_key, long_url, timeout=60 * 60 * 24)

    res = {
        "url": short_url
    }
    return json.dumps(res)


def short_2_long_service(short_key):
    long_url = cache.get(short_key)
    if not long_url:
        instance = Long2Short.objects.get(short_key=short_key)
        long_url = instance.long_url

        cache.set(short_key, long_url, timeout=60 * 60 * 24)

    return long_url


def long_2_short_v2_service(long_url, ip_address):
    # 查询缓存，如果 short_url 存在，则返回 short_url
    short_url = cache.get(long_url)
    if short_url:
        res = {
            "url": short_url
        }
        return json.dumps(res)

    # 保存数据到数据库
    instance = Long2ShortV2(
        long_url=long_url,
        created_at=timezone.now(),
        ip_address=ip_address,
    )
    instance.save()
    instance_id = instance.id
    short_key = id_2_short_key(instance_id)
    short_url = DOMAIN + short_key

    # 更新缓存
    cache.set(long_url, short_url, timeout=60 * 60 * 24)
    cache.set(short_key, long_url, timeout=60 * 60 * 24)

    res = {
        "url": short_url
    }
    return json.dumps(res)


def short_2_long_v2_service(short_key):
    long_url = cache.get(short_key)
    if long_url:
        return long_url
    else:
        instance_id = short_key_2_id(short_key)
        instance = Long2ShortV2.objects.get(id=instance_id)
        long_url = instance.long_url

        # 更新缓存
        cache.set(short_key, long_url, timeout=60 * 60 * 24)
        return long_url
