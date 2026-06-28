from apps.core.base_classes.base_serializer import BaseModelSerializer
from apps.smoothing.models import Smoothing


class SmoothingSerializer(BaseModelSerializer):
    class Meta:
        model = Smoothing
        fields = "__all__"