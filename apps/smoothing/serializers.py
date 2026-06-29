from apps.core.base_classes.base_serializer import BaseModelSerializer
from apps.smoothing.models import Smoothing, Branch, Colleague


class SmoothingSerializer(BaseModelSerializer):
    class Meta:
        model = Smoothing
        fields = "__all__"


class BranchSerializer(BaseModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"
        read_only_fields = ["smoothing"]


class ColleagueSerializer(BaseModelSerializer):
    class Meta:
        model = Colleague
        fields = "__all__"
        read_only_fields = ["branch"]
