from rest_framework import viewsets, views
from rest_framework.response import Response

from apps.core.permissions import IsSuperUser

from apps.owner.models import UsageMethod, Version, SupportInformation
from apps.owner.serializers import UsageMethodSerializer, VersionSerializer, SupportInformationSerializer


class UsageMethodViewSet(viewsets.ModelViewSet):
    queryset = UsageMethod.objects.all()
    serializer_class = UsageMethodSerializer
    permission_classes = (IsSuperUser,)


class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    permission_classes = (IsSuperUser,)


class SupportInformationView(views.APIView):
    permission_classes = (IsSuperUser,)

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
