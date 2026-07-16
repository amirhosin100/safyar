import functools
import random

from apps.core.tests.base_test import APIRequestData, InitialData
from apps.smoothing.tests.fixtures.data import smoothing_initial_data
from apps.wallet.choices import TransactionStatusChoices, TransactionTypeChoices
from apps.wallet.models import WalletTransaction, Wallet

wallet_initial_data = InitialData(
    Wallet,
    {
        "stock": 1000
    },
    relation_fields={
        "smoothing": smoothing_initial_data
    }
)

wallet_transaction_initial_data = APIRequestData(
    WalletTransaction,
    {
        "amount": 1000,
        "status": TransactionStatusChoices.SUCCESS,
        "transaction_type": TransactionTypeChoices.SETTLE,
        "description": "test description",
        "tracking_code": functools.partial(random.randint, 1, 100)
    },
    relation_fields={
        "wallet": wallet_initial_data
    },
    extra_fields=["id", "created_at", "updated_at", "wallet"]
)
