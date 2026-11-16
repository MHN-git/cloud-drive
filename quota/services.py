from django.core.cache import cache

from quota.models import Quota


def get_user_quota_data(owner_id):
    cache_key = cache.make_key(f"user:{owner_id}:quota")
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    try:
        quota = Quota.objects.get(owner_id=owner_id)
    except Quota.DoesNotExist:
        return None

    available_bytes = (
        quota.quota_limit_bytes
        - quota.used_bytes
        - quota.reserved_bytes
    )

    data = {
        "quota_limit_bytes": quota.quota_limit_bytes,
        "used_bytes": quota.used_bytes,
        "reserved_bytes": quota.reserved_bytes,
        "available_bytes": available_bytes,
    }

    cache.set(cache_key, data, timeout=300)
    return data