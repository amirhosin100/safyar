from django.core.validators import RegexValidator
from django.db import models
from rest_framework.exceptions import ValidationError

from apps.account.choices import OwnerRequestChoices, UserTypeChoices
from apps.core.models import BaseManager, BaseModel
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager, BaseManager):
    def create_user(self, national_code, phone_number, password=None, **extra_fields):
        """
        Creates and saves a User with the given national_code, date of
        birth and password.
        """
        if not national_code:
            raise ValueError("Users must have an national_code")

        user = self.model(
            national_code=national_code,
            phone_number=phone_number,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, national_code, phone_number, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given national_code, date of
        birth and password.
        """
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_superuser", False):
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(
            national_code=national_code,
            password=password,
            phone_number=phone_number,
            **extra_fields,
        )
        return user


class User(AbstractBaseUser, PermissionsMixin):
    national_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='Only numbers are allowed.'
            )
        ],
        verbose_name=_("national code"),
    )
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        verbose_name=_("phone number"),
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                message=_("your phone number is invalid. correct is 09xxxxxxxxx")
            )
        ]
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name=_("full name"),
    )
    user_type = models.CharField(
        max_length=10,
        choices=UserTypeChoices.choices,
        default=UserTypeChoices.NORMAL,
        verbose_name=_("User type"),
    )

    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "national_code"
    REQUIRED_FIELDS = ["phone_number", "full_name"]

    def __str__(self):
        return self.national_code

    def is_staff(self):
        return self.is_superuser

    def save(self, *args, **kwargs):
        print(self.phone_number)
        if not self.phone_number:
            raise ValidationError("phone_number is required")
        if self.is_superuser:
            self.user_type = UserTypeChoices.SUPER_USER

        super().save(*args, **kwargs)


class OwnerRequest(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        verbose_name=_("user"),
        related_name="request",
    )
    submit_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("submit date"),
        help_text=_("for owner users")
    )
    status = models.CharField(
        choices=OwnerRequestChoices.choices,
        max_length=2,
        default=OwnerRequestChoices.PENDING,
        verbose_name=_("Status"),
    )
