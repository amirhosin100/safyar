from apps.core.models import BaseModel
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.validations import phone_number_validator
from apps.smoothing.choices import ClosedDayChoices, OrderChoices, JobTypeChoices, SmoothingStatusChoices


class Smoothing(BaseModel):
    logo = models.ImageField(
        verbose_name=_("Logo"),
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Branch Name"),
        null=True,
        blank=True,
    )
    owner_name = models.CharField(
        max_length=255,
        verbose_name=_("Owner Name"),
        blank=True,
    )
    landline_number = models.CharField(
        max_length=20,
        verbose_name=_("Landline Number"),
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        max_length=11,
        verbose_name=_("Phone Number"),
        validators=[phone_number_validator],
        null=True,
        blank=True,
    )
    city = models.CharField(
        max_length=20,
        verbose_name=_("City"),
        null=True,
        blank=True,
    )
    address = models.TextField(
        max_length=1000,
        verbose_name=_("Address")
    )
    status = models.PositiveSmallIntegerField(
        editable=False,
        choices=SmoothingStatusChoices.choices,
        default=0,
        verbose_name=_("status")
    )
    wallet_stock = models.PositiveBigIntegerField(
        editable=False,
        verbose_name=_("Wallet Stock"),
        default=0
    )

    def save(self, *args, **kwargs):
        if self.wallet_stock == 0:
            self.status = SmoothingStatusChoices.DEACTIVATED
        else:
            self.status = SmoothingStatusChoices.ACTIVATED

        super().save(*args, **kwargs)


class Branch(BaseModel):
    smoothing = models.ForeignKey(
        Smoothing,
        on_delete=models.PROTECT,
        related_name="branches",
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name")
    )
    closed_days = models.CharField(
        max_length=10,
        verbose_name=_("Closed Days"),
        choices=ClosedDayChoices.choices,
        default=ClosedDayChoices.NO_DAYS_OFF,
    )
    open_time = models.TimeField(
        verbose_name=_("Open time"),
        null=True,
        blank=True
    )
    closed_time = models.TimeField(
        verbose_name=_("Closed time"),
        null=True,
        blank=True
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_("Order"),
        choices=OrderChoices.choices,
    )
    first_follow_up_code = models.PositiveBigIntegerField(
        verbose_name=_("First Follow Up Code"),
        null=True,
        blank=True
    )
    next_follow_up_code = models.PositiveBigIntegerField(
        verbose_name=_("Next Follow Up Code"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")

    def __str__(self):
        return f"{self.user.full_name} - {self.name}"


class Colleague(BaseModel):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="colleagues",
        verbose_name=_("Branch"),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )
    phone_number = models.CharField(
        max_length=11,
        verbose_name=_("Phone Number"),
        validators=[phone_number_validator]
    )
    job_type = models.CharField(
        max_length=20,
        verbose_name=_("Job Type"),
        choices=JobTypeChoices.choices
    )
