from rest_framework import viewsets
from apps.core.permissions import IsSuperUser

from apps.owner.models import UsageMethod, Version
from apps.owner.serializers import UsageMethodSerializer, VersionSerializer


class UsageMethodViewSet(viewsets.ModelViewSet):
    queryset = UsageMethod.objects.all()
    serializer_class = UsageMethodSerializer
    permission_classes = (IsSuperUser,)


class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    permission_classes = (IsSuperUser,)
