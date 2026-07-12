from django.core.cache import cache
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

from apps.core.utils import prefix

phone_number_validator = RegexValidator(
    r'^09\d{9}$',
    message=_("your phone number is invalid. correct is 09xxxxxxxxx")
)
national_code_validator = RegexValidator(
    regex=r'^\d{10}$',
    message=_('national code must have 10 characters')
)
plate_validator = RegexValidator(
    regex=r'^\d{2}-.*-\d{3}-\d{2}$',
    message=_('plate should like this xx-<letter>-xxx-xx')
)
image_format_validator = FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])


def validate_image_size_2m(image):
    max_size = 2 * 1024 * 1024

    if image.size > max_size:
        raise DjangoValidationError(_("Image size must not exceed 2MB."))


def validate_image_size_10m(image):
    max_size = 10 * 1024 * 1024

    if image.size > max_size:
        raise DjangoValidationError(_("Image size must not exceed 10MB."))


def password_validator(password1, password2):
    if password1 != password2:
        raise serializers.ValidationError(_("Passwords don't match"))

    try:
        validate_password(password1)
    except DjangoValidationError as e:
        raise serializers.ValidationError(_("please fix these %s") % str(e.messages))


def validate_verify_code(national_code, code):
    real_code = cache.get(prefix.verify_code.format(national_code=national_code))
    if not real_code or real_code != code:
        raise serializers.ValidationError(_("code is invalid or expired"))

    return True


def delete_verify_code(national_code):
    cache.delete(prefix.verify_code.format(national_code=national_code))
