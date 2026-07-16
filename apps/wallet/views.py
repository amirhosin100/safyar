import logging
from django.urls import reverse
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.permissions import HasBranch, IsSuperUser
from apps.core.base_classes.base_viewset import BaseAPIView
from apps.core.utils.pagination import OptionalPageNumberPagination
from apps.wallet.choices import TransactionStatusChoices, TransactionTypeChoices
from apps.wallet.models import WalletTransaction, Wallet
from apps.wallet.serializers import (
    WalletTransactionSuperUserSerializer,
    WalletTransactionSerializer,
    AddStockWalletSerializer,
    ChargeWalletSerializer,
    WalletSerializer
)

from azbankgateways import (
    bankfactories,
    models as bank_models,
    default_settings as settings,
)
from azbankgateways.exceptions import AZBankGatewaysException, BankGatewayStateInvalid


class WalletTransactionSuperUserListView(ListAPIView, BaseAPIView):
    pagination_class = OptionalPageNumberPagination
    permission_classes = (IsSuperUser,)
    queryset = WalletTransaction.objects.select_related("wallet__smoothing")

    def get_serializer_class(self):
        return WalletTransactionSuperUserSerializer


class WalletTransactionListView(ListAPIView, BaseAPIView):
    pagination_class = OptionalPageNumberPagination
    serializer_class = WalletTransactionSerializer
    permission_classes = (HasBranch,)
    queryset = WalletTransaction.objects.select_related("wallet__smoothing")

    def get_queryset(self):
        smoothing = self.request.user.active_branch.smoothing
        return self.queryset.filter(wallet__smoothing=smoothing)


class WalletTransactionRetrieveView(RetrieveAPIView, BaseAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = (HasBranch,)
    queryset = WalletTransaction.objects.select_related("wallet__smoothing")

    def get_queryset(self):
        smoothing = self.request.user.active_branch.smoothing
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
                    "detail": _("smoothing not found")
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AddStockWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        wallet.stock += amount
        wallet.save()
        wallet.transactions.create(
            amount=amount,
            status=TransactionStatusChoices.SUCCESS,
            transaction_type=TransactionTypeChoices.SETTLE,
            description="واریز  کیف پول توسط ادمین",
        )

        res_serializer = AddStockWalletSerializer(instance=wallet)
        return Response(res_serializer.data)


class WalletInfoView(APIView):
    permission_classes = (HasBranch,)
    serializer_class = WalletSerializer

    def get(self, request):
        wallet = request.user.active_branch.smoothing.wallet
        serializer = WalletSerializer(instance=wallet)

        return Response(serializer.data)


class ChargeWalletView(APIView):
    # TODO write test for it
    permission_classes = (HasBranch,)
    serializer_class = ChargeWalletSerializer

    def post(self, request):
        serializer = ChargeWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        smoothing = request.user.active_branch.smoothing

        if smoothing is None:
            return Response({"detail": _("you don't have a smoothing")}, status=status.HTTP_403_FORBIDDEN)

        if not hasattr(smoothing, "owner_user"):
            return Response({"detail": _("smoothing is unknown")}, status=status.HTTP_403_FORBIDDEN)

        phone_number = smoothing.owner_user.phone_number
        factory = bankfactories.BankFactory()

        try:
            bank = factory.auto_create()
            bank.set_request(request)
            bank.set_amount(amount)
            bank.set_client_callback_url(reverse("wallet:callback-gateway"))
            bank.set_mobile_number(phone_number)

            context = bank.get_gateway()

            WalletTransaction.objects.create(
                amount=amount,
                status=TransactionStatusChoices.PENDING,
                transaction_type=TransactionTypeChoices.SETTLE,
                description=_(
                    "user with name {full_name} charge the wallet"
                ).format(full_name=request.user.full_name),
                tracking_code=bank.get_tracking_code()
            )

            return Response(context)

        except AZBankGatewaysException as e:
            logging.critical(e)
            return Response(
                {"detail": "an error occurred when opening the gateway"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class CallBackWalletView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        tracking_code = request.GET.get(settings.TRACKING_CODE_QUERY_PARAM, None)
        if not tracking_code:
            return Response({"detail": "This link is invalid"}, status=status.HTTP_404_NOT_FOUND)

        factory = bankfactories.BankFactory()
        bank = factory.create()

        try:
            bank.verify(tracking_code)
            bank_record = bank_models.Bank.objects.get(tracking_code=tracking_code)
        except BankGatewayStateInvalid:
            return Response({"detail": "This link is invalid"}, status=status.HTTP_404_NOT_FOUND)

        if bank_record.is_success:
            transaction = WalletTransaction.objects.get(tracking_code=tracking_code)
            transaction.status = TransactionStatusChoices.SUCCESS
            transaction.save()

            wallet = transaction.wallet
            amount = bank_record.amount
            wallet.add(amount)

            return redirect(settings.WALLET_CALLBACK_URL + f"?tracking_code={tracking_code}")

        return Response({"detail": "the operation has been failed"}, status=status.HTTP_400_BAD_REQUEST)
