from rest_framework import serializers
from apps.owner.models import UsageMethod, Version


class UsageMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMethod
        fields = "__all__"

class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = "__all__"