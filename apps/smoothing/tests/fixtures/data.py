from apps.core.tests.image import create_image
from apps.core.tests.base_test import APIRequestData, InitialData
from apps.smoothing.choices import SmoothingStatusChoices
from apps.smoothing.models import Smoothing, Branch

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
        "wallet_stock": 0,
    },
    {
        "name": "test",
        "owner_name": "test owner",
        "landline_number": "035-36200000",
        "phone_number": "09123456789",
        "city": "yazd",
        "address": "yazd",
        "status": SmoothingStatusChoices.DEACTIVATED,
        "wallet_stock": 0,
        "deleted": False,
        "is_active": True,
    },
    extra_fields=["created_at", "updated_at", "id", "logo"]
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
        "deleted": False,
        "is_active": True,
    },
    extra_fields=["created_at", "updated_at", "id", "logo"]
)
branch_initial_data = InitialData(
    Branch,
    {
        "name": "test",
        "order": 1,
        "open_time": "10:20:00",
        "closed_time": "20:00:00"
    },
    relation_fields={
        "smoothing": smoothing_initial_data
    }
)
branch_create_data = APIRequestData(
    Branch,
    {
        "name": "test 2",
        "order": 2,
        "open_time": "10:20:00",
        "closed_time": "20:00:00"
    },
    relation_fields={
        "smoothing": smoothing_create_data
    }
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
        "status": 0,
        "wallet_stock": 0,
        "deleted": False,
        "is_active": True,
    },
    extra_fields=["created_at", "updated_at", "id", "logo"]
)
