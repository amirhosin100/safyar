from django.urls import path
from apps.wallet.views import (
    WalletTransactionRetrieveView,
    WalletTransactionListView,
    WalletTransactionSuperUserListView,
    AddStockWalletView,
    ChargeWalletView, WalletInfoView
)

app_name = "wallet"

urlpatterns = [
    path("owner/wallet/transcations/", WalletTransactionSuperUserListView.as_view(), name="owner-transaction-list"),
    path("owner/wallet/charge/<int:smoothing_id>/", AddStockWalletView.as_view(), name="charge-wallet"),
    path("wallet/transcations/", WalletTransactionListView.as_view(), name="transaction-list"),
    path("wallet/transcation/<int:pk>/", WalletTransactionRetrieveView.as_view(), name="transaction-retrieve"),
    path("wallet/charge/", ChargeWalletView.as_view(), name="charge-user-wallet"),
    path("wallet/", WalletInfoView.as_view(), name="wallet-info"),
]
