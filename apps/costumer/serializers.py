from rest_framework import serializers

from apps.costumer.models import Costumer, Car


class CostumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Costumer
        read_only_fields = ("branch",)
        exclude = ("deleted",)


class CarSerializer(serializers.ModelSerializer):
    costumer = CostumerSerializer(many=False, read_only=True)

    class Meta:
        model = Car
        fields = (
            "id",
            "costumer",
            "plate",
            "color",
            "name"
        )


class CarSimpleSerializer(CarSerializer):
    pass
