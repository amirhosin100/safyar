import datetime

from django.utils import timezone
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.base_classes.base_viewset import BaseProtectionViewSet
from apps.core.permissions import HasBranch
from apps.core.wallet import WalletCenter
from apps.project.choices import ProjectStatusChoices
from apps.project.models import Project, MainPart, ProjectImage, FixItem
from apps.project.serializers import ProjectSerializer, FixItemSerializer, MainPartSerializer, ProjectImageSerializer, \
    ScheduleRequestSerializer
from django.utils.translation import gettext_lazy as _

from apps.smoothing.models import Branch


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

        status = serializer.validated_data['status']

        if status == ProjectStatusChoices.DELIVERED:
            raise ValidationError(_("your choices are `CANCELED` `TURNED` & `SUBMITTED`"))

        wallet = WalletCenter(self.request.user.active_branch.smoothing.wallet)

        match status:
            case ProjectStatusChoices.CANCELED.value:
                wallet.decrease_canceled_project()
            case ProjectStatusChoices.TURNED.value:
                wallet.decrease_turned_project()
            case ProjectStatusChoices.SUBMITTED.value:
                wallet.decrease_accepted_project()

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


class ProjectScheduleListView(APIView):
    permission_classes = (HasBranch,)

    def get(self, request):
        serializer = ScheduleRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        branch_id = serializer.validated_data['branch_id']
        month = int(serializer.validated_data['month'])
        year = int(serializer.validated_data['year'])

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response(
                data={"detail": _("Branch not found")},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.check_object_permissions(request, branch)

        if branch.open_time is None or branch.closed_time is None:
            return Response(
                {"detail": _("This branch has not open or closed time.,Please Set these Fields")},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = datetime.datetime(month=month, year=year, day=1)
        times = {}
        week_days = branch.get_closed_days()

        while start_date.month == month:
            time = branch.open_time.replace(second=0, microsecond=0)
            str_time = start_date.strftime("%Y-%m-%d")
            if start_date.weekday() in week_days:
                start_date += datetime.timedelta(days=1)
                continue
            times[str_time] = set()

            while time < branch.closed_time:
                times[str_time].add(time.strftime("%H:%M"))
                minutes = time.minute + time.hour * 60 + 30
                time = datetime.time(minute=minutes % 60, hour=minutes // 60)

            start_date += datetime.timedelta(days=1)

        dates = Project.objects.filter(
            branch=branch,
            turn_time__month=month,
            turn_time__year=year,
        ).values_list("turn_time", flat=True)

        for date in dates:
            date = timezone.localtime(date)
            day = datetime.datetime(month=date.month, year=date.year, day=date.day)
            day = day.strftime("%Y-%m-%d")
            hour = datetime.time(hour=date.hour, minute=date.minute)
            hour = hour.strftime("%H:%M")

            if day in times and hour in times[day]:
                times[day].remove(hour)

        return Response(data=times, status=status.HTTP_200_OK)
