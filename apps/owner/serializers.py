from rest_framework import serializers
from apps.owner.models import UsageMethod, Version, SupportInformation


class UsageMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMethod
        fields = "__all__"


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = "__all__"


class SupportInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportInformation
        fields = [
            "landline_number",
            "phone_number",
            "email",
            "accountability_time",
        ]
