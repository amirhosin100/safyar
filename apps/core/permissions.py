from rest_framework import permissions

from apps.account.choices import UserTypeChoices
from apps.smoothing.models import Smoothing, Branch


class IsSuperUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser




class IsNotNormalUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if (
                    request.user.user_type != UserTypeChoices.NORMAL and
                    hasattr(request.user, "branch")
            ):
                return True
        return False


class HasBranch(permissions.IsAuthenticated):
    """
        use this for objects which has branch attribute or itself is a branch
    """

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.branch is not None:
                return True
        return False

    def has_object_permission(self, request, view, obj):
        branch = obj if isinstance(obj, Branch) else obj.branch

        if request.user.user_type in [UserTypeChoices.OWNER, UserTypeChoices.SUPER_USER]:
            return request.user.smoothing == branch.smoothing

        return request.user.allowed_branches.filter(id=branch.id).exists()
