import requests
import logging

from .base import AbstractSMS
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSIR(AbstractSMS):
    def __init__(
            self,
            api_key: str,
            line_number: int,
            verify_template_id: str = "123456",
            verify_sms_key="Code",
    ):
        if api_key is None:
            raise ValueError("api_key is required")
        if line_number is None:
            raise ValueError("line_number is required")
        if verify_template_id is None:
            raise ValueError("verify_template_id is required")
        self.api_key = api_key
        self.line_number = line_number
        self.verify_template_id = verify_template_id
        self.verify_sms_key = verify_sms_key

        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "Accept": "application/json",
        }
        self.real_sending = True

    def send_single_sms(self, phone_number: str, message: str) -> bool:
        url = "https://api.sms.ir/v1/send/bulk"
        message = self.add_static_message(message)
        data = {
            "lineNumber": self.line_number,
            "messageText": message,
            "mobiles": [phone_number],
        }
        return self._send_request("POST", url, data)

    def send_bulk_sms(
            self, phone_numbers: list | tuple, message: str, time=None
    ) -> bool:
        url = "https://api.sms.ir/v1/send/bulk"
        message = self.add_static_message(message)
        data = {
            "lineNumber": self.line_number,
            "messageText": message,
            "sendDateTime": time,
            "mobiles": phone_numbers,
        }

        return self._send_request("POST", url, data)

    def cancel_bulk_sms(self, identifier: str) -> bool:
        url = f"https://api.sms.ir/v1/send/scheduled/{identifier}"
        return self._send_request("DELETE", url)

    def send_verification_code(self, phone_number: str, code: str) -> bool:
        url = "https://api.sms.ir/v1/send/verify"
        data = {
            "mobile": phone_number,
            "templateId": self.verify_template_id,
            "parameters": [{"name": self.verify_sms_key, "value": code}],
        }
        return self._send_request("POST", url, data)

    def _send_request(self, method, url, data=None) -> bool:
        if self.real_sending:
            response = requests.request(method, url, headers=self.headers, json=data)
            return self._check_response(response)
        return True

    @staticmethod
    def _check_response(response: requests.Response) -> bool:
        code = response.json()["status"]
        status = code == 1
        if not status:
            match code:
                case 101:
                    logger.error("sms detail : %s",response.json())
                case _:
                    logger.critical("sms detail : %s", response.json())

        return status

    @staticmethod
    def add_static_message(text: str) -> str:
        cancel_message = "لغو 11"
        site_message = settings.SITE_URL
        return text + f"\n {cancel_message} \n {site_message}"
