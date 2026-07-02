from rest_framework import serializers
from apps.project.models import Project, MainPart, FixArea, ProjectImage, FixItem


class FixItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixItem
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    fix_items = FixItemSerializer(many=True, read_only=True)

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
            "fix_items",
        ]


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
        fields = ["name", "id"]


class MainPartSerializer(serializers.ModelSerializer):
    fix_areas = FixAreaSerializer(many=True, read_only=True)

    class Meta:
        model = MainPart
        fields = ["name", "fix_areas", ]
