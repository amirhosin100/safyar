"""
these models will be used in help page
just superusers could add or change these models
"""

from apps.core.models import BaseModel
from django.db import models

from apps.core.validations import phone_number_validator


class SupportInformation(BaseModel):
    landline_number = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    phone_number = models.CharField(
        max_length=11,
        validators=[phone_number_validator],
        null=True,
        blank=True
    )
    email = models.EmailField(
        null=True,
        blank=True
    )
    accountability_time = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


class UsageMethod(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField()


class Version(BaseModel):
    version_number = models.CharField(max_length=20)
    date = models.DateField()
    description = models.TextField()
