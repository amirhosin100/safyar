from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.base_classes.base_viewset import BaseProtectionViewSet
from apps.core.permissions import IsSuperUser, IsNotNormalUser, HasBranch, IsOwner, IsOwnerOrSuperUser
from apps.core.sms import sms_class, schedule_bulk_sms
from apps.costumer.models import Costumer
from apps.owner.choices import SmsTypeChoices, SmsLogStatusChoices
from apps.owner.models import SmsLog
from apps.smoothing.models import Smoothing, Branch, Colleague
from apps.smoothing.serializers import (
    SmoothingSerializer,
    BranchSerializer,
    ColleagueSerializer,
    SmoothingSuperUserSerializer, SmsSerializer
)


class SmoothingViewSet(BaseProtectionViewSet):
    queryset = Smoothing.objects.all()
    permission_classes = (IsSuperUser,)

    def get_serializer_class(self):
        return SmoothingSuperUserSerializer


class BranchViewSet(BaseProtectionViewSet):
    serializer_class = BranchSerializer
    permission_classes = (HasBranch & IsNotNormalUser,)
    queryset = Branch.objects.all()

    def perform_create(self, serializer):
        smoothing = self.request.user.active_branch.smoothing
        serializer.save(smoothing=smoothing)

    def get_queryset(self):
        return self.queryset.filter(pk__in=self.request.user.allowed_branches.values_list("pk", flat=True))


class ColleagueViewSet(BaseProtectionViewSet):
    serializer_class = ColleagueSerializer
    permission_classes = (HasBranch | IsSuperUser,)
    queryset = Colleague.objects.all()

    def get_queryset(self):
        return self.queryset.filter(branch__in=self.request.user.allowed_branches.values_list("pk", flat=True))


class SmoothingAPIView(APIView):
    """
    for editing smoothing in settings
    """
    permission_classes = (IsOwner,)
    serializer_class = SmoothingSerializer

    @staticmethod
    def edit(request, partial):
        smoothing = request.user.smoothing

        serializer = SmoothingSerializer(instance=smoothing, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def get(self, request):
        smoothing = request.user.smoothing
        serializer = SmoothingSerializer(instance=smoothing)
        return Response(serializer.data)

    def put(self, request):
        return self.edit(request, partial=False)

    def patch(self, request):
        return self.edit(request, partial=True)


class BranchAPIView(APIView):
    """
    for editing branch in settings
    """
    permission_classes = (IsNotNormalUser,)
    serializer_class = BranchSerializer

    @staticmethod
    def edit(request, partial):
        branch = request.user.active_branch

        serializer = BranchSerializer(instance=branch, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def get(self, request):
        branch = request.user.active_branch
        serializer = BranchSerializer(instance=branch)
        return Response(serializer.data)

    def put(self, request):
        return self.edit(request, partial=False)

    def patch(self, request):
        return self.edit(request, partial=True)


# TODO add decrease wallet
class SendBulkSMSAPIView(APIView):
    permission_classes = (IsOwnerOrSuperUser,)

    def post(self, request):
        serializer = SmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]

        phone_numbers = Costumer.objects.filter(
            branch__smoothing=request.user.smoothing,
        ).values_list("phone_number", flat=True)

        result = schedule_bulk_sms(phone_numbers, message)

        if not all(result):
            SmsLog.objects.create_log(
                user=request.user,
                message=message,
                sms_type=SmsTypeChoices.BULK,
                status=SmsLogStatusChoices.FAILED
            )
            return Response({
                "detail": "messages didn't send successfully",
                "pack": result
            },
                status=status.HTTP_400_BAD_REQUEST
            )
        SmsLog.objects.create_log(user=request.user, message=message, sms_type=SmsTypeChoices.BULK)

        return Response({
            "detail": "messages sent successfully",
        })


class SendSingleSMSAPIView(APIView):
    permission_classes = (HasBranch, IsNotNormalUser)

    def post(self, request, costumer_id):
        serializer = SmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]

        try:
            costumer = Costumer.objects.get(pk=costumer_id)
        except Costumer.DoesNotExist:
            return Response({
                "detail": _("costumer does not exist"),
            },status=status.HTTP_404_NOT_FOUND)

        if costumer.branch not in request.user.allowed_branches.all():
            return Response(
                {"detail": _("you don't have permission to send sms messages for this costumer"), },
                status=status.HTTP_403_FORBIDDEN
            )

        result = sms_class.send_single_sms(costumer.phone_number, message)

        if not result:
            return Response(
                {"detail": _("messages didn't send")},
                status=status.HTTP_400_BAD_REQUEST
            )
        SmsLog.objects.create_log(user=request.user, message=message, sms_type=SmsTypeChoices.SINGLE)

        return Response({
            "detail": _("messages sent successfully"),
        })
