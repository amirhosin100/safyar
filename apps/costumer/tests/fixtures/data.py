from apps.costumer.choices import GenderChoices
from apps.costumer.models import Costumer, Car
from apps.core.tests.base_test import InitialData, APIRequestData
from apps.smoothing.tests.fixtures.data import branch_initial_data

costumer_initial_data = InitialData(
    Costumer,
    {
        "name": "ali",
        "gender": GenderChoices.MALE,
        "phone_number": "09136633332",
        "address": "test address",
    },
    {
        "name": "ali",
        "gender": GenderChoices.MALE.value,
        "phone_number": "09136633332",
        "address": "test address",
    },
    relation_fields={
        "branch": branch_initial_data
    },
    extra_fields=["branch", "id", "created_at", "updated_at"],
)

costumer_create_data = APIRequestData(
    Costumer,
    {
        "name": "ali",
        "gender": GenderChoices.MALE,
        "phone_number": "09136633315",
        "address": "test address",
    },
    {
        "name": "ali",
        "gender": GenderChoices.MALE.value,
        "phone_number": "09136633315",
        "address": "test address",
    },
    extra_fields=["branch", "id", "created_at", "updated_at"],
)

car_initial_data = InitialData(
    Car,
    {
        "plate": "11-الف-555-45",
        "color": "red",
        "name":"test"
    },
    relation_fields={
        "costumer": costumer_initial_data,
    },
    extra_fields=["costumer", "id", "created_at", "updated_at"],
)

car_create_data = APIRequestData(
    Car,
    {
        "plate": "12-الف-555-45",
        "color": "red",
        "name":"test"
    },
    relation_fields={
        "costumer": costumer_initial_data,
    },
    extra_fields=["costumer", "id", "created_at", "updated_at"],
)
