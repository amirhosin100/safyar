from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

from apps.core.validations import phone_number_validator, plate_validator
from apps.costumer.choices import GenderChoices


class Costumer(BaseModel):
    branch = models.ForeignKey(
        "smoothing.Branch",
        on_delete=models.CASCADE,
        verbose_name=_("Branch"),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )
    gender = models.CharField(
        max_length=1,
        verbose_name=_("Gender"),
        choices=GenderChoices.choices,
    )
    phone_number = models.CharField(
        max_length=11,
        verbose_name=_("Phone Number"),
        validators=[phone_number_validator]
    )
    address = models.TextField(
        max_length=1000,
        verbose_name=_("Address"),
    )

    class Meta:
        verbose_name = _("Costumer")
        verbose_name_plural = _("Costumers")
        unique_together = (("branch", "phone_number"),)

    def __str__(self):
        return self.name


class Car(BaseModel):
    costumer = models.ForeignKey(
        Costumer,
        on_delete=models.CASCADE,
        verbose_name=_("Costumer"),
        related_name="cars",
    )
    plate = models.CharField(
        max_length=30,
        verbose_name=_("Plate"),
        validators=[plate_validator],
    )
    color = models.CharField(
        max_length=30,
        verbose_name=_("Color"),
    )

    class Meta:
        verbose_name = _("Car")
        verbose_name_plural = _("Cars")

    def __str__(self):
        return self.plate


    @property
    def branch(self):
        return self.costumer.branch