import datetime

from django.core.validators import RegexValidator
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from apps.project.choices import ProjectStatusChoices
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

    def validate(self, attrs):
        if "turn_time" not in attrs:
            return attrs

        turn_time = attrs["turn_time"]
        branch = attrs["branch"]

        closed_time = branch.closed_time
        open_time = branch.open_time

        if closed_time is None or open_time is None:
            raise ValidationError(_("You must declare closed_time and open_time for branch and save project"))

        if turn_time is not None:
            turn_time = parse_datetime(str(turn_time))
            turn_time = turn_time.replace(microsecond=0, second=0)

            if turn_time.minute not in [0, 30]:
                raise ValidationError(_("turn_time must be 0 or 30"))

            time = datetime.time(hour=turn_time.hour, minute=turn_time.minute)
            if not (closed_time >= time >= open_time):
                raise ValidationError(_("turn_time must between %s and %s") % (str(open_time), str(closed_time)))

            attrs["turn_time"] = str(turn_time)

        return attrs


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
    areas = FixAreaSerializer(many=True, read_only=True)

    class Meta:
        model = MainPart
        fields = ["name", "areas"]


class ScheduleRequestSerializer(serializers.Serializer):
    year = serializers.CharField(validators=[RegexValidator(regex=r"^\d{4}$")])
    month = serializers.CharField(validators=[RegexValidator(regex=r"^(0?[1-9]|1[0-2])$")])
    branch_id = serializers.BigIntegerField()
