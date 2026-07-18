from rest_framework import viewsets, views
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from apps.account.models import User
from apps.core.permissions import IsSuperUser, IsSuperUserOrReadOnly
from apps.core.base_classes.base_viewset import BaseProtectionViewSet, BaseAPIView
from apps.core.utils.pagination import OptionalPageNumberPagination

from apps.owner.models import UsageMethod, Version, SupportInformation, SmsLog
from apps.owner.serializers import UsageMethodSerializer, VersionSerializer, SupportInformationSerializer, \
    UserOwnerSerializer, SmsLogSerializer


class UsageMethodViewSet(viewsets.ModelViewSet):
    queryset = UsageMethod.objects.all()
    serializer_class = UsageMethodSerializer
    permission_classes = (IsSuperUserOrReadOnly,)


class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    permission_classes = (IsSuperUserOrReadOnly,)


class SmsLogListView(ListAPIView, BaseAPIView):
    pagination_class = OptionalPageNumberPagination
    serializer_class = SmsLogSerializer
    permission_classes = (IsSuperUser,)
    queryset = SmsLog.objects.select_related("send_by", "branch__smoothing")


class SupportInformationView(views.APIView):
    permission_classes = (IsSuperUserOrReadOnly,)
    serializer_class = SupportInformationSerializer

    @staticmethod
    def edit(request, partial):
        support_info = SupportInformation.objects.first()
        serializer = SupportInformationSerializer(instance=support_info, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get(self, request):
        support_info = SupportInformation.objects.first()
        serializer = SupportInformationSerializer(instance=support_info)
        return Response(serializer.data)

    def put(self, request):
        return self.edit(request, partial=False)

    def patch(self, request):
        return self.edit(request, partial=True)


class UserOwnerViewSet(BaseProtectionViewSet):
    queryset = User.objects.select_related("active_branch")
    serializer_class = UserOwnerSerializer
    permission_classes = (IsSuperUser,)
