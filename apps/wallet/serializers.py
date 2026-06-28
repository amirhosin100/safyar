from apps.core.base_classes.base_serializer import BaseModelSerializer
from rest_framework import serializers
from apps.wallet.models import WalletTransaction


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
