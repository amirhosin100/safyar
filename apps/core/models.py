from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseQuerySet(models.QuerySet):
    def start_at(self, start_datetime: datetime):
        if start_datetime:
            return self.filter(created_at__gte=start_datetime)
        return self

    def end_at(self, end_datetime: datetime):
        if end_datetime:
            return self.filter(created_at__lte=end_datetime)
        return self


class BaseManager(models.Manager):
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("Timestamp when the record was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
        help_text=_("Last time the record was saved."),
    )
    objects = BaseManager()

    @staticmethod
    def get_write_only_fields() -> tuple:
        return tuple()

    class Meta:
        abstract = True
