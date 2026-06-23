from django.utils.translation import gettext_lazy as _
from django.db import models

class GenderChoices(models.TextChoices):
    MALE = "M", _("Male")
    FEMALE = "F", _("Female")