from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.base_classes.base_viewset import BaseProtectionViewSet
from apps.core.permissions import HasBranch
from apps.project.models import Project, MainPart, ProjectImage, FixItem
from apps.project.serializers import ProjectSerializer, FixItemSerializer, MainPartSerializer, ProjectImageSerializer
from django.utils.translation import gettext_lazy as _


# TODO write some tests for these
class ProjectViewSet(BaseProtectionViewSet):
    queryset = Project.objects.prefetch_related("items")
    serializer_class = ProjectSerializer
    permission_classes = (HasBranch,)

    def get_queryset(self):
        return self.queryset.filter(
            smoothing=self.request.user.active_branch.smoothing,
            branch__in=self.request.user.allowed_branches.all()
        )

    def perform_create(self, serializer):
        car = serializer.validated_data['car']
        user = serializer.context['request'].user
        if car.branch.smoothing != user.active_branch.smoothing and not user.is_superuser:
            raise PermissionDenied(_("You don't have permission to create project for this car"))
        serializer.save()


class ProjectImageViewSet(BaseProtectionViewSet):
    queryset = ProjectImage.objects.all()
    serializer_class = ProjectImageSerializer
    permission_classes = (HasBranch,)

    def get_queryset(self):
        return self.queryset.filter(
            project__smoothing=self.request.user.active_branch.smoothing,
            project__branch__in=self.request.user.allowed_branches.all()
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.validated_data['project']
        if (
                project.branch not in request.user.allowed_branches.all()
                or project.smoothing != request.user.active_branch.smoothing
        ):
            raise PermissionDenied(_("You don't have permission to create image for this project"))

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FixItemViewSet(BaseProtectionViewSet):
    queryset = FixItem.objects.all()
    serializer_class = FixItemSerializer
    permission_classes = (HasBranch,)

    def get_queryset(self):
        return self.queryset.filter(
            project__smoothing=self.request.user.active_branch.smoothing,
            project__branch__in=self.request.user.allowed_branches.all()
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.validated_data['project']
        if (
                project.branch not in request.user.allowed_branches.all()
                or project.smoothing != request.user.active_branch.smoothing
        ):
            raise PermissionDenied(_("You don't have permission to create FixItem for this Project"))

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MainPartListView(generics.ListAPIView):
    queryset = MainPart.objects.prefetch_related("areas")
    serializer_class = MainPartSerializer
    permission_classes = (IsAuthenticated,)
