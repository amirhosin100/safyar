from django.urls import path
from apps.wallet.views import (
    WalletTransactionRetrieveView,
    WalletTransactionListView,
    WalletTransactionSuperUserListView
)

app_name = "wallet"

urlpatterns = [
    path("owner/wallet/transcations/",WalletTransactionSuperUserListView.as_view(),name="owner-transaction-list"),
    path("wallet/transcations/",WalletTransactionListView.as_view(),name="transaction-list"),
    path("wallet/transcation/<int:pk>/",WalletTransactionRetrieveView.as_view(),name="transaction-retrieve"),
]
