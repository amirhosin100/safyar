from django.db import models
from django.utils.translation import gettext_lazy as _


class ClosedDayChoices(models.TextChoices):
    FRIDAY = "FR", _("friday")
    THURSDAY = "TH", _("thursday")
    FRIDAY_AND_THURSDAY = "FR&TH", _("friday and thursday")
    NO_DAYS_OFF = "NO", _("no days off")


class OrderChoices(models.IntegerChoices):
    MAIN = 1, _("main")
    OTHER = 2, _("other")


class JobTypeChoices(models.TextChoices):
    SMOOTHER = "smoother", _("Smoother")
    PAINTER = "painter", _("Painter")
    MASKER = "masker", _("Masker")


class SmoothingStatusChoices(models.IntegerChoices):
    DEACTIVATED = 0, _("Deactivated")
    ACTIVATED = 1, _("Activated")
