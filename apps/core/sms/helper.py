import ast
import uuid

from apps.core.utils import prefix
from .sms_services import SMSIR
import os
from django_redis import get_redis_connection

redis = get_redis_connection("default")


def get_sms_class():
    api_key = os.environ.get("SMS_API_KEY")
    line_number = int(os.environ.get("SMS_LINE_NUMBER"))
    verify_template_id = os.environ.get("SMS_VERIFY_TEMPLATE_ID", "123456")

    sms_class = SMSIR(api_key, line_number, verify_template_id)
    return sms_class


sms_class = get_sms_class()


def schedule_bulk_sms(phone_numbers, message):
    list_phone_numbers = []
    random_key = str(uuid.uuid4())
    data = {"message": message}

    counter = 0
    while phone_numbers:
        slice_phone_numbers = phone_numbers[0:100]
        list_phone_numbers.append(slice_phone_numbers)
        phone_numbers = phone_numbers[100:]

        data["phone_numbers"] = slice_phone_numbers
        redis.hset(prefix.sms_bulk.format(id=random_key), counter, str(data))
        counter += 1

    for counter, phone_numbers in enumerate(list_phone_numbers):
        result = sms_class.send_bulk_sms(phone_numbers, message)
        if result:
            redis.hdel(prefix.sms_bulk.format(id=random_key), counter + 1)


def get_not_sent_sms():
    keys = redis.keys(prefix.sms_bulk_all)
    data = []

    for key in keys:
        sms_dict = redis.hgetall(key)
        for key, value in sms_dict.items():
            value = ast.literal_eval(value.decode())
            data.append(value)

    return data
