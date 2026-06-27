from django.db import models
from django.utils.translation import gettext_lazy as _


class FuelTypeChoices(models.TextChoices):
    FULL = 'FULL', _('Full')
    THREE_QUARTERS = 'THREE_QUARTER', _('Three Quarter')
    HALF = 'HALF', _('Half')
    ONE_QUARTER = 'ONE_QUARTER', _('One Quarter')
    EMPTY = 'EMPTY', _('Empty')


class TemporalChoices(models.TextChoices):
    AFTER = 'AF', _('After')
    BEFORE = 'BF', _('Before')


class FixTypeChoices(models.TextChoices):
    SMOOTHING = 'SMOOTHING', _('Smoothing')
    MASK = 'MASK', _('Mask')
    PAINT = 'PAINT', _('Paint')


class ProjectStatusChoices(models.TextChoices):
    CANCELED = 'CANCELED', _('Canceled')
    TURNED = 'TURNED', _('Turned')
    SUBMITTED = 'SUBMITTED', _('Submitted')
    DELIVERED = 'DELIVERED', _('Delivered')
