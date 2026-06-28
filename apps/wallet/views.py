from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.mixins import ListModelMixin

from apps.core.permissions import HasBranch, IsSuperUser
from apps.core.base_classes.base_viewset import BaseAPIView
from apps.core.utils.pagination import OptionalPageNumberPagination
from apps.wallet.models import WalletTransaction
from apps.wallet.serializers import (
    WalletTransactionSuperUserSerializer,
    WalletTransactionSerializer
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
