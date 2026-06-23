from django.db import models


class OwnerRequestChoices(models.TextChoices):
    ACCEPTED = "AC", "accepted"
    REJECTED = "RJ", "rejected"
    PENDING = "PN", "pending"

class UserTypeChoices(models.TextChoices):
    SUPER_USER = "SU", "superuser"
    OWNER = "OW", "owner"
    ADMIN = "AD", "admin"
    NORMAL = "NM", "normal"