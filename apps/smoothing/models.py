import datetime

from apps.core.models import BaseModel
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.validations import phone_number_validator, validate_image_size_2m, image_format_validator
from apps.smoothing.choices import ClosedDayChoices, OrderChoices, JobTypeChoices, SmoothingStatusChoices


class Smoothing(BaseModel):
    logo = models.ImageField(
        verbose_name=_("Logo"),
        null=True,
        blank=True,
        validators=[
            validate_image_size_2m,
            image_format_validator
        ]
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
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
    )

    def save(self, *args, **kwargs):
        if self.wallet_stock == 0:
            self.status = SmoothingStatusChoices.DEACTIVATED
        else:
            self.status = SmoothingStatusChoices.ACTIVATED

        super().save(*args, **kwargs)
        self._pre_is_active = self.is_active

        if self.branches.count() == 0:
            Branch.objects.create(
                name="شعبه مرکزی",
                smoothing=self,
                order=1,
            )

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._pre_is_active = instance.is_active
        return instance


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
        default=datetime.time(hour=8, minute=30),
    )
    closed_time = models.TimeField(
        verbose_name=_("Closed time"),
        default=datetime.time(hour=20, minute=0),
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_("Order"),
        choices=OrderChoices.choices,
    )

    next_follow_up_code = models.PositiveBigIntegerField(
        verbose_name=_("Next Follow Up Code"),
        default=1000
    )
    address = models.TextField(
        max_length=1000,
        verbose_name=_("Address"),
        null=True,
        blank=True
    )
    call_number = models.CharField(
        max_length=15,
        verbose_name=_("Call Number"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")

    def __str__(self):
        return self.name

    def get_closed_days(self):
        match self.closed_days:
            case ClosedDayChoices.NO_DAYS_OFF:
                return []
            case ClosedDayChoices.FRIDAY:
                return [4]
            case ClosedDayChoices.THURSDAY:
                return [3]
            case ClosedDayChoices.FRIDAY_AND_THURSDAY:
                return [4, 3]

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._pre_next_follow_up_code = instance.next_follow_up_code
        return instance


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
