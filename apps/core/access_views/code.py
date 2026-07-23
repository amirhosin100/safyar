from uuid import uuid4
from django_redis import get_redis_connection
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from apps.core.utils.prefix import access_code, access_codes

redis = get_redis_connection()


def generate_identify(obj, expire_time=None):
    if expire_time is not None:
        expire_time = localtime(expire_time)
        now = timezone.now()

        expire_time = expire_time - now
        if expire_time.total_seconds() <= 1:
            raise ValueError("Expire time must be greater than 1")

    identify = str(uuid4())
    redis.set(access_code.format(identify=identify), obj.id, ex=expire_time)

    if expire_time is None:
        key = access_codes.format(object_id=obj.id, model_name=obj.__class__.__name__)
        redis.sadd(key, identify)

    return identify


def get_identify(identify: str):
    value = redis.get(access_code.format(identify=identify))
    if value is None:
        return 404, _("this code is invalid or expired")

    value = value.decode()
    if not value.isdigit():
        return 400, {"detail": _("this code is invalid")}

    value = int(value)
    return 200, value
