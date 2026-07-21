from uuid import uuid4
from django_redis import get_redis_connection
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from apps.core.utils.prefix import access_code

redis = get_redis_connection()
date_format = "%Y-%m-%d %H:%M:%S %z"


def generate_identify(object_id, expire_time):
    expire_time = localtime(expire_time)
    now = timezone.now()

    expire_time = expire_time - now
    if expire_time.total_seconds() <= 1:
        raise ValueError("Expire time must be greater than 1")

    identify = uuid4()
    redis.set(access_code.format(identify=identify), object_id, ex=expire_time)

    return identify


def get_identify(identify: str):
    value = redis.get(access_code.format(identify=identify))
    if value is None:
        return False, _("this code is invalid or expired")

    value = value.decode()
    if not value.isdigit():
        return False, {"detail":_("this code is invalid")}

    value = int(value)
    return True, value
