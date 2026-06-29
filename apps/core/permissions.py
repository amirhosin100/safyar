from rest_framework import permissions

from apps.account.choices import UserTypeChoices
from apps.smoothing.models import Smoothing


class IsSuperUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


class IsJoinedToSmoothingOrBranch(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            if isinstance(obj, Smoothing) and obj.user == request.use:
                return True
        return False


class IsOwner(permissions.IsAuthenticated, IsJoinedToSmoothingOrBranch):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.user_type == UserTypeChoices.OWNER:
                return True
        return False


class IsAdminOrOwner(permissions.IsAuthenticated, IsJoinedToSmoothingOrBranch):
    """
    Admin != superuser or staff
    """

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if (
                    request.user.user_type in [UserTypeChoices.OWNER, UserTypeChoices.ADMIN] and
                    hasattr("branch", request.user)
            ):
                return True
        return False


class HasBranch(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.branch is not None:
                return True
        return False
