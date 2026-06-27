from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

phone_number_validator = RegexValidator(
    r'^09\d{9}$',
    message=_("your phone number is invalid. correct is 09xxxxxxxxx")
)
national_code_validator = RegexValidator(
    regex=r'^\d{10}$',
    message=_('national code must have 10 characters')
)