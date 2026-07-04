from rest_framework import serializers

from apps.costumer.models import Costumer, Car


class CostumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Costumer
        fields = "__all__"
        read_only_fields = ("branch",)


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = "__all__"