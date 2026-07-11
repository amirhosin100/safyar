from rest_framework import serializers

from apps.core.base_classes.base_serializer import BaseModelSerializer
from apps.smoothing.models import Smoothing, Branch, Colleague


class SmoothingSerializer(BaseModelSerializer):
    class Meta:
        model = Smoothing
        exclude = ("deleted",)
        read_only_fields = ("is_active",)


class SmoothingSuperUserSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Smoothing
        fields = "__all__"


class BranchSerializer(BaseModelSerializer):
    class Meta:
        model = Branch
        read_only_fields = ["smoothing"]
        exclude = ("deleted",)


class BranchUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name"]
        read_only_fields = ["id", "name"]


class ColleagueSerializer(BaseModelSerializer):
    class Meta:
        model = Colleague
        exclude = ("deleted",)


class SmsSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)

