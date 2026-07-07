from .sms_services import SMSIR
import os


def get_sms_class():
    api_key = os.environ.get("SMS_API_KEY")
    line_number = int(os.environ.get("SMS_LINE_NUMBER"))
    verify_template_id = os.environ.get("SMS_VERIFY_TEMPLATE_ID","123456")

    sms_class = SMSIR(api_key, line_number, verify_template_id)
    return sms_class
