from apps.core.tests.base_test import InitialData, APIRequestData
from apps.owner.models import Version, UsageMethod

version_initial_data = InitialData(
    Version,
    {
        "version_number": "1.0.0",
        "date": "2023-01-01",
        "description": "Initial version of the application."
    }
)

version_create_data = APIRequestData(
    Version,
    {
        "version_number": "2.0.0",
        "date": "2024-01-01",
        "description": "updated version of the application."
    }
)
usage_method_initial_data = InitialData(
    UsageMethod,
    {
        "title": "How to use the application",
        "description": "This is a guide on how to use the application."
    }
)
usage_method_create_data = APIRequestData(
    UsageMethod,
    {
        "title": "How to use the application 2",
        "description": "This is a guide on how to use the application. 2"
    }
)
