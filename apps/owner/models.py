"""
these models will be used in help page
just superusers could add or change these models
"""
from apps.core.models import BaseModel, BaseManager
from django.db import models

from apps.core.validations import phone_number_validator
from apps.owner.choices import SmsTypeChoices
from django.utils.translation import gettext_lazy as _


class SmsManager(BaseManager):
    def create_log(self, user, message, sms_type):
        sms = self.get_queryset().create(
            send_by=user,
            branch=user.active_branch,
            message=message,
            sms_type=sms_type,
        )
        return sms


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


class SmsLog(BaseModel):
    message = models.TextField(
        verbose_name=_("Message"),
    )
    sms_type = models.CharField(
        max_length=2,
        choices=SmsTypeChoices.choices,
        verbose_name=_("SMS Type"),
    )
    branch = models.ForeignKey(
        "smoothing.Branch",
        on_delete=models.PROTECT,
        verbose_name=_("Branch"),
        related_name="sms_logs"
    )
    send_by = models.ForeignKey(
        "account.User",
        on_delete=models.PROTECT,
        verbose_name=_("Send By User"),
    )
    objects = SmsManager()

    class Meta:
        verbose_name = _("Sms Log")
        verbose_name_plural = _("Sms Logs")
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_sms_type_display()} - {self.created_at}"
