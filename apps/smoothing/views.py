from apps.core.base_classes.base_viewset import BaseProtectionViewSet
from apps.core.permissions import IsSuperUser
from apps.smoothing.models import Smoothing
from apps.smoothing.serializers import SmoothingSerializer


class SmoothingViewSet(BaseProtectionViewSet):
    serializer_class = SmoothingSerializer
    queryset = Smoothing.objects.all()
    permission_classes = (IsSuperUser,)


