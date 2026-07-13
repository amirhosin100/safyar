from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .values import (
    SUBMIT_CANCELED_PROJECT,
    SUBMIT_TURNED_PROJECT,
    SUBMIT_ACCEPTED_PROJECT,
    SEND_SINGLE_SMS,
    SEND_BULK_SMS,
)


class WalletCenter:
    def __init__(self, wallet):
        self.wallet = wallet

    def decrease_canceled_project(self):
        if not self.wallet.decrease(SUBMIT_CANCELED_PROJECT):
            raise ValidationError(_("You can't add canceled project, because your wallet stock is empty"))

    def decrease_turned_project(self):
        if not self.wallet.decrease(SUBMIT_TURNED_PROJECT):
            raise ValidationError(_("You can't add turned project, because your wallet stock is empty"))

    def decrease_accepted_project(self):
        if not self.wallet.decrease(SUBMIT_ACCEPTED_PROJECT):
            raise ValidationError(_("You can't add accepted project, because your wallet stock is empty"))

    def decrease_single_sms(self):
        if not self.wallet.decrease(SEND_SINGLE_SMS):
            raise ValidationError(_("You can't send single sms, because your wallet stock less then from the price"))

    def decrease_bulk_sms(self, number):
        if not self.wallet.decrease(SEND_BULK_SMS * number):
            raise ValidationError(_("You can't send bulk sms, because your wallet stock less then from the price"))
