from rest_framework.exceptions import ValidationError

from apps.core.base_classes.base_serializer import BaseModelSerializer
from rest_framework import serializers
from apps.wallet.models import WalletTransaction, Wallet


class WalletTransactionSerializer(BaseModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            "wallet",
            "amount",
            "status",
            "transaction_type",
            "description",
        ]


class WalletTransactionSuperUserSerializer(WalletTransactionSerializer):
    smoothing_name = serializers.SerializerMethodField()

    class Meta:
        model = WalletTransaction
        fields = WalletTransactionSerializer.Meta.fields + ["smoothing_name"]

    def get_smoothing(self, obj):
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
