from rest_framework import serializers

from apps.account.models import User
from apps.owner.models import UsageMethod, Version, SupportInformation, SmsLog
from apps.smoothing.serializers import BranchSerializer


class UsageMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMethod
        exclude = ("deleted",)


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        exclude = ("deleted",)


class SmsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsLog
        exclude = ("deleted",)


class SupportInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportInformation
        fields = [
            "landline_number",
            "phone_number",
            "email",
            "accountability_time",
        ]


class UserOwnerSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "national_code",
            "phone_number",
            "full_name",
            "branch",
            "created_at",
            "is_active",
            "branch",
        ]
