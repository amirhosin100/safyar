from .helper import sms_class
from .messages import (
    CANCELED_PROJECT,
    ACCEPTED_PROJECT,
    TURNED_PROJECT,
    WALLET_STOCK_WARN,
    WALLET_STOCK_EMPTY,
    REGISTER_USER_FOR_SUPER_USER,
    REGISTER_SMS,
    ACCEPTED_SMOOTHING,
    REJECTED_SMOOTHING,
    SMOOTHING_DEACTIVATED,
    SMOOTHING_ACTIVATED,
)


class SMSCenter:
    """
    use this for sending simple sms
    """

    def __init__(self):
        self.sms = sms_class

    def _send_sms(self, phone_number, message):
        return self.sms.send_single_sms(phone_number, message)

    def send_canceled_project_sms(self, project):
        phone_number = project.car.costumer.phone_number
        return self._send_sms(phone_number, CANCELED_PROJECT)

    def send_accepted_project_sms(self, project):
        phone_number = project.car.costumer.phone_number
        return self._send_sms(phone_number, ACCEPTED_PROJECT)

    def send_turned_project_sms(self, project):
        phone_number = project.car.costumer.phone_number
        # TODO make this to persian language
        time = str(project.turn_time)
        return self._send_sms(phone_number, TURNED_PROJECT % time)

    def send_wallet_stock_waring_sms(self, wallet):
        phone_number = wallet.smoothing.owner_user.phone_number
        stock = wallet.stock
        return self._send_sms(phone_number, WALLET_STOCK_WARN % stock)

    def send_wallet_stock_empty_sms(self, wallet):
        phone_number = wallet.smoothing.owner_user.phone_number
        return self._send_sms(phone_number, WALLET_STOCK_EMPTY)

    def send_register_smoothing_for_super_user(self, user, superuser):
        phone_number = superuser.phone_number
        return self._send_sms(phone_number, REGISTER_USER_FOR_SUPER_USER % user.full_name)

    def send_register_sms(self, user):
        phone_number = user.phone_number
        return self._send_sms(phone_number, REGISTER_SMS)

    def send_accepted_smoothing_sms(self, user):
        phone_number = user.phone_number
        return self._send_sms(phone_number, ACCEPTED_SMOOTHING)

    def send_rejected_smoothing_sms(self, user):
        phone_number = user.phone_number
        return self._send_sms(phone_number, REJECTED_SMOOTHING)

    def send_smoothing_deactivated_sms(self, user):
        phone_number = user.phone_number
        return self._send_sms(phone_number, SMOOTHING_DEACTIVATED)

    def send_smoothing_activated_sms(self, user):
        phone_number = user.phone_number
        return self._send_sms(phone_number, SMOOTHING_ACTIVATED)

sms_center = SMSCenter()