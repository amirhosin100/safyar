from apps.account.tests.fixtures.data import user_initial_data
from apps.core.tests.image import create_image
from apps.core.tests.base_test import APIRequestData, InitialData
from apps.smoothing.choices import SmoothingStatusChoices
from apps.smoothing.models import Smoothing

smoothing_initial_data = InitialData(
    Smoothing,
    {
        "logo": create_image(),
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "035-36200000",
        "phone_number": "09123456789",
        "city": "yazd",
        "address": "yazd",
        "status": SmoothingStatusChoices.ACTIVATED,
        "wallet_stock": 2000,
    },
    {
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "035-36200000",
        "phone_number": "09123456789",
        "city": "yazd",
        "address": "yazd",
        "status": SmoothingStatusChoices.ACTIVATED,
        "wallet_stock": 2000,
    },
    relation_fields={
        "user": user_initial_data
    },
    extra_fields=["user", "created_at", "updated_at", "id", "logo"]
)

smoothing_create_data = APIRequestData(
    Smoothing,
    {
        "logo": create_image(),
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "021-36200000",
        "phone_number": "09193456789",
        "city": "yazd",
        "address": "yazd",
        "status": SmoothingStatusChoices.ACTIVATED,
        "wallet_stock": 2000,
    },
    {
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "021-36200000",
        "phone_number": "09193456789",
        "city": "yazd",
        "address": "yazd",
        "status": 0,
        "wallet_stock": 0,
    },
    relation_fields={
        "user": user_initial_data
    },
    extra_fields=["user", "created_at", "updated_at", "id", "logo"]
)
smoothing_update_data = APIRequestData(
    Smoothing,
    {
        "logo": create_image(),
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "021-36200000",
        "phone_number": "09193456789",
        "city": "yazd",
        "address": "yazd",
        "status": SmoothingStatusChoices.ACTIVATED,
        "wallet_stock": 3000,
    },
    {
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "021-36200000",
        "phone_number": "09193456789",
        "city": "yazd",
        "address": "yazd",
        "status": 1,
        "wallet_stock": 2000,
    },
    relation_fields={
        "user": user_initial_data
    },
    extra_fields=["user", "created_at", "updated_at", "id", "logo"]
)