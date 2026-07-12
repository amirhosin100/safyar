from django.db import models
from rest_framework.exceptions import ValidationError

from apps.core.models import BaseModel
from apps.project.choices import FuelTypeChoices, FixTypeChoices, ProjectStatusChoices, TemporalChoices

from django.utils.translation import gettext_lazy as _

from apps.smoothing.models import Branch


class Project(BaseModel):
    branch = models.ForeignKey(
        "smoothing.Branch",
        on_delete=models.PROTECT,
        verbose_name=_("Branch"),
        related_name='projects',
    )
    smoothing = models.ForeignKey(
        "smoothing.Smoothing",
        on_delete=models.PROTECT,
        verbose_name=_("Smoothing"),
        related_name='projects',
        editable=False
    )
    car = models.ForeignKey(
        "costumer.Car",
        on_delete=models.PROTECT,
        verbose_name=_("Car"),
    )

    kilometer_of_car = models.IntegerField(
        verbose_name=_("Kilometer Of Car"),
    )
    fuel_value = models.CharField(
        max_length=20,
        verbose_name=_("Fuel Value"),
        choices=FuelTypeChoices.choices
    )
    turn_time = models.DateTimeField(
        verbose_name=_("Turn Time"),
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        verbose_name=_("Status"),
        choices=ProjectStatusChoices.choices
    )
    fee = models.PositiveIntegerField(
        verbose_name=_("Fee"),
        default=0,
        editable=False
    )
    reason_of_cancelled = models.TextField(
        verbose_name=_("Reason Of Cancelled"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        indexes = [
            models.Index(fields=["smoothing", "branch"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.car} | {self.created_at}"

    def save(self, *args, **kwargs):
        branch = Branch.objects.get(id=self.branch_id)
        self.smoothing = branch.smoothing

        if self.status != ProjectStatusChoices.CANCELED and self.reason_of_cancelled:
            raise ValidationError(_("You just can write reason when status is CANCELED"))

        super().save(*args, **kwargs)


class ProjectImage(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("Project"),
        related_name='images',
    )
    image = models.ImageField(
        upload_to='images/project',
    )
    temporal = models.CharField(
        max_length=20,
        verbose_name=_("Temporal"),
        choices=TemporalChoices.choices,
    )

    @property
    def branch(self):
        return self.project.branch

    @property
    def smoothing(self):
        return self.project.smoothing

    class Meta:
        verbose_name = _("ProjectImage")
        verbose_name_plural = _("ProjectImages")
        indexes = [
            models.Index(fields=["project"]),
        ]


class MainPart(BaseModel):
    name = models.CharField(
        max_length=50,
        verbose_name=_("Main part"),
    )


class FixArea(BaseModel):
    main_part = models.ForeignKey(
        MainPart,
        on_delete=models.CASCADE,
        related_name="areas",
        verbose_name=_("Main Part"),
    )
    name = models.CharField(
        max_length=70,
        verbose_name=_("Name"),
    )

    class Meta:
        verbose_name = _("FixArea")
        verbose_name_plural = _("FixArea")

    def __str__(self):
        return f"{self.main_part.name} | {self.name}"


class FixItem(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("Project"),
        related_name='items',
    )
    fix_type = models.CharField(
        max_length=20,
        verbose_name=_("Fix Type"),
        choices=FixTypeChoices.choices,
    )
    fix_area = models.ForeignKey(
        FixArea,
        on_delete=models.PROTECT,
        verbose_name=_("Fix Area"),
    )
    discount = models.PositiveIntegerField(
        verbose_name=_("Discount"),
        default=0,
    )
    repairman = models.ForeignKey(
        "smoothing.Colleague",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    number_of_days = models.PositiveSmallIntegerField(verbose_name=_("Number of Days"))
    amount = models.PositiveIntegerField(verbose_name=_("Amount"))

    @property
    def branch(self):
        return self.project.branch

    class Meta:
        verbose_name = _("FixItem")
        verbose_name_plural = _("FixItems")
        indexes = [
            models.Index(fields=["project"]),
        ]
