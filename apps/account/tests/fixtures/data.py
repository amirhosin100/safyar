from apps.core.tests.base_test import InitialData, APIRequestData
from apps.account.models import User

user_initial_data = InitialData(
    User,
    {
        "national_code": "1238867890",
        "phone_number": "09121234567",
        "full_name": "علی محمدی",
    },
)
