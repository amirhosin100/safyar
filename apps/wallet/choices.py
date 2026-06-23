from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionStatusChoices(models.TextChoices):
    SUCCESS = 'SU', _('Success')
    FAILED = 'FD', _('Failed')
    PENDING = 'PN', _('Pending')


class TransactionTypeChoices(models.TextChoices):
    SETTLE = 'SETTLE', _('Settle')
    WITHDRAW = 'WITHDRAW', _('Withdraw')
