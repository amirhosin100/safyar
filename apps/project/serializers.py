from django.core.validators import RegexValidator
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from apps.project.models import Project, MainPart, FixArea, ProjectImage, FixItem
from apps.smoothing.models import Branch
from django.utils.translation import gettext_lazy as _


class FixItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixItem
        exclude = ("deleted",)


class ProjectSerializer(serializers.ModelSerializer):
    items = FixItemSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "created_at",
            "branch",
            "smoothing",
            "car",
            "kilometer_of_car",
            "fuel_value",
            "turn_time",
            "status",
            "fee",
            "items",
        ]

    def validate_turn_time(self, value):
        if value is not None and value.minute not in [0, 30]:
            raise ValidationError(_("turn_time must be 0 or 30"))
        return value


class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage
        fields = [
            "id",
            "project",
            "image",
            "temporal"
        ]


class FixAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixArea
        fields = ["name", "id", "main_part"]


class MainPartSerializer(serializers.ModelSerializer):
    fix_areas = FixAreaSerializer(many=True, read_only=True)

    class Meta:
        model = MainPart
        fields = ["name", "fix_areas"]


class ScheduleRequestSerializer(serializers.Serializer):
    year = serializers.CharField(validators=[RegexValidator(regex=r"^\d{4}$")])
    month = serializers.CharField(validators=[RegexValidator(regex=r"^(0?[1-9]|1[0-2])$")])
    branch_id = serializers.BigIntegerField()
