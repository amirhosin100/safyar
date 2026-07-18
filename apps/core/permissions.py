from rest_framework import permissions

from apps.account.choices import UserTypeChoices
from apps.account.models import User
from apps.smoothing.models import Smoothing, Branch


class IsSuperUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


class IsSuperUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return user and user.is_authenticated and user.is_superuser


class IsOwner(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.user_type == UserTypeChoices.OWNER


class IsOwnerOrSuperUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.user_type in [UserTypeChoices.OWNER, UserTypeChoices.SUPER_USER]:
                return True
        return False


class IsNotNormalUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if (
                    request.user.user_type != UserTypeChoices.NORMAL and
                    hasattr(request.user, "active_branch")
            ):
                return True
        return False


class HasBranch(permissions.IsAuthenticated):
    """
        use this for objects which has branch attribute or itself is a branch
    """

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.active_branch is not None:
                return True
        return False

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Branch):
            branch = obj
        elif isinstance(obj, User):
            branch = obj.active_branch
        else:
            branch = obj.branch

        if request.user.user_type in [UserTypeChoices.OWNER, UserTypeChoices.SUPER_USER]:
            return request.user.smoothing == branch.smoothing

        return request.user.allowed_branches.filter(id=branch.id).exists()
