from abc import ABC, abstractmethod


class AbstractSMS(ABC):

    @abstractmethod
    def send_single_sms(self, phone_number: str, message: str) -> bool:
        pass

    @abstractmethod
    def send_bulk_sms(self, phone_numbers: list | tuple, message: str) -> bool:
        pass

    @abstractmethod
    def send_verification_code(self, phone_number: str, code: str) -> bool:
        pass

    @abstractmethod
    def _send_request(self, method, url, data=None) -> bool:
        pass
