from apps.core.base_classes.base_serializer import BaseModelSerializer
from apps.smoothing.models import Smoothing, Branch


class SmoothingSerializer(BaseModelSerializer):
    class Meta:
        model = Smoothing
        fields = "__all__"
        read_only_fields = ["user"]


class BranchSerializer(BaseModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"
        read_only_fields = ["smoothing"]
