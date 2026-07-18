import datetime

from django.core.validators import RegexValidator
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from apps.project.models import Project, MainPart, FixArea, ProjectImage, FixItem
from django.utils.translation import gettext_lazy as _

from apps.smoothing.serializers import ColleagueSerializer


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
            "amount",
            "items",
            "code",
            "amount_paid",
            "remaining_amount"
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


class ProjectListSerializer(ProjectSerializer):
    owner_name = serializers.SerializerMethodField(read_only=True)
    owner_phone_number = serializers.SerializerMethodField(read_only=True)
    colleagues = ColleagueSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ProjectSerializer.Meta.fields + [
            "owner_name",
            "owner_phone_number",
            "smoothing_days",
            "smoothing_price",
            "mask_days",
            "mask_price",
            "paint_days",
            "paint_price",
            "colleagues"
        ]

    def get_owner_name(self, obj):
        return obj.car.costumer.name

    def get_owner_phone_number(self, obj):
        return obj.car.costumer.phone_number


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


class ProjectScheduleTimeSerializer(serializers.Serializer):
    time = serializers.CharField(
        validators=[RegexValidator(r"^[0-2][0-9]:[0-5][0-9]$")]
    )


class ProjectScheduleSerializer(serializers.Serializer):
    times = ProjectScheduleTimeSerializer(many=True, read_only=True)
    date = serializers.DateField(read_only=True)
