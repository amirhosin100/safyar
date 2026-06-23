from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.utils.translation import gettext_lazy as _

from apps.account.models import User


class UserCreationForm(BaseUserCreationForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    class Meta:
        model = User
        fields = ["national_code", "phone_number","full_name"]


class UserChangeForm(BaseUserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["national_code", "password","user_type", "is_active", "phone_number", "full_name"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ["national_code", "full_name", "is_superuser"]
    list_filter = ["is_superuser"]
    fieldsets = (
        (None, {"fields": ("national_code", "password")}),
        (_("Personal info"), {"fields": ("full_name", "phone_number", "user_type")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("national_code","phone_number","full_name", "password1", "password2"),
            },
        ),
    )
    search_fields = ["national_code"]
    ordering = ["national_code"]
    filter_horizontal = []


admin.site.register(User, UserAdmin)