from rest_framework import serializers

from apps.core.validations import plate_validator
from apps.costumer.choices import GenderChoices
from apps.costumer.models import Costumer, Car


class CostumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Costumer
        read_only_fields = ("branch",)
        exclude = ("deleted",)


class CarSerializer(serializers.ModelSerializer):
    costumer_detail = CostumerSerializer(many=False, read_only=True)

    class Meta:
        model = Car
        fields = (
            "id",
            "costumer",
            "plate",
            "color",
            "name",
            "costumer_detail"
        )


class CarSimpleSerializer(CarSerializer):
    pass


class AddCostumerSerializer(serializers.Serializer):
    branch = serializers.BigIntegerField(required=True)
    costumer_name = serializers.CharField(required=True)
    gender = serializers.ChoiceField(required=True,choices=GenderChoices.choices)
    phone_number = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    car_name = serializers.CharField(required=True)
    plate = serializers.CharField(required=True, validators=[plate_validator])
    color = serializers.CharField(required=True)
