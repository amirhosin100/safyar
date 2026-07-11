from django.db import models
from django.utils.translation import gettext_lazy as _


class SmsTypeChoices(models.TextChoices):
    BULK = "BU", _("Bulk")
    SINGLE = "SI", _("Single")


class SmsLogStatusChoices(models.TextChoices):
    SUCCESS = "SU", _("Success")
    FAILED = "FA", _("Failed")