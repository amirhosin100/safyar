from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasBranch, IsSuperUser
from apps.core.base_classes.base_viewset import BaseAPIView
from apps.core.utils.pagination import OptionalPageNumberPagination
from apps.wallet.models import WalletTransaction, Wallet
from apps.wallet.serializers import (
    WalletTransactionSuperUserSerializer,
    WalletTransactionSerializer, AddStockWalletSerializer
)


# TODO write tests for these
class WalletTransactionSuperUserListView(ListAPIView, BaseAPIView):
    pagination_class = OptionalPageNumberPagination
    serializer_class = WalletTransactionSuperUserSerializer
    permission_classes = (IsSuperUser,)
    queryset = WalletTransaction.objects.select_related("wallet__smoothing")


class WalletTransactionListView(ListAPIView, BaseAPIView):
    pagination_class = OptionalPageNumberPagination
    serializer_class = WalletTransactionSerializer
    permission_classes = (HasBranch,)
    queryset = WalletTransaction.objects.select_related("wallet__smoothing")

    def get_queryset(self):
        smoothing = self.request.user.branch.smoothing
        return self.queryset.filter(wallet__smoothing=smoothing)


class WalletTransactionRetrieveView(RetrieveAPIView, BaseAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = (HasBranch,)
    queryset = WalletTransaction.objects.select_related("wallet__smoothing")

    def get_queryset(self):
        smoothing = self.request.user.branch.smoothing
        return self.queryset.filter(wallet__smoothing=smoothing)


class AddStockWalletView(APIView):
    permission_classes = (IsSuperUser,)
    serializer_class = AddStockWalletSerializer

    def post(self, request, smoothing_id):
        try:
            wallet = Wallet.objects.get(smoothing_id=smoothing_id)
        except Wallet.DoesNotExist:
            return Response(
                data={
                    "error": "smoothing not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AddStockWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet.stock += serializer.validated_data["amount"]
        wallet.save()

        res_serializer = AddStockWalletSerializer(instance=wallet)
        return Response(res_serializer.data)
