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
    user_full_name = serializers.SerializerMethodField()
    user_national_code = serializers.SerializerMethodField()
    smoothing_name = serializers.SerializerMethodField()

    class Meta:
        model = SmsLog
        exclude = ("deleted",)


    def get_user_full_name(self, obj):
        return obj.send_by.full_name

    def get_user_national_code(self, obj):
        return obj.send_by.national_code

    def get_smoothing_name(self, obj):
        return obj.branch.smoothing.name


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
    active_branch = BranchSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "national_code",
            "phone_number",
            "full_name",
            "active_branch",
            "is_active",
        ]
