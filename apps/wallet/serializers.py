from rest_framework.exceptions import ValidationError

from rest_framework import serializers
from apps.wallet.models import WalletTransaction, Wallet


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "wallet",
            "amount",
            "status",
            "transaction_type",
            "description",
            "created_at",
        ]


class WalletTransactionSuperUserSerializer(WalletTransactionSerializer):
    smoothing_name = serializers.SerializerMethodField()

    class Meta:
        model = WalletTransaction
        fields = WalletTransactionSerializer.Meta.fields + ["smoothing_name"]

    def get_smoothing_name(self, obj):
        return obj.wallet.smoothing.name


class AddStockWalletSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = Wallet
        fields = ["stock", "amount"]
        read_only_fields = ["stock"]

    def validate_amount(self, amount):
        if amount < 0:
            raise ValidationError("Amount must be greater then zero")

        return amount


class ChargeWalletSerializer(serializers.Serializer):
    amount = serializers.BigIntegerField()
