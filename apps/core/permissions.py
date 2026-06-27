from rest_framework import permissions

from apps.account.choices import UserTypeChoices


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_superuser:
                return True
        return False

class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.user_type == UserTypeChoices.OWNER:
                return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            if hasattr(obj, "branch") and obj.branch.smoothing.user == request.user:
                return True
            if hasattr(obj, "smoothing") and obj.smoothing.user == request.user:
                return True
        return False

