from apps.core.tests.base_test import InitialData, APIRequestData
from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.choices import FuelTypeChoices, ProjectStatusChoices
from apps.project.models import Project
from apps.smoothing.tests.fixtures.data import branch_initial_data

project_initial_data = InitialData(
    Project,
    {
        "kilometer_of_car": 200,
        "fuel_value": FuelTypeChoices.FULL,
        "turn_time": "2001-10-20",
        "status": ProjectStatusChoices.TURNED,
        "fee": 100,
    },
    {
        "kilometer_of_car": 200,
        "fuel_value": FuelTypeChoices.FULL.value,
        "turn_time": "2001-10-20T00:00:00+03:30",
        "status": ProjectStatusChoices.TURNED.value,
        "fee": 100,
    },
    relation_fields={
        "car": car_initial_data,
        "branch": branch_initial_data
    },
    extra_fields=["car", "branch", "smoothing", "created_at","items", "id"],
)

project_create_data = APIRequestData(
    Project,
    {
        "kilometer_of_car": 300,
        "fuel_value": FuelTypeChoices.FULL,
        "turn_time": "2001-10-30",
        "status": ProjectStatusChoices.TURNED,
    },
    {
        "kilometer_of_car": 300,
        "fuel_value": FuelTypeChoices.FULL.value,
        "turn_time": "2001-10-30T00:00:00+03:30",
        "status": ProjectStatusChoices.TURNED.value,
    },
    relation_fields={
        "car": car_initial_data,
        "branch": branch_initial_data
    },
    extra_fields=["car", "branch", "smoothing", "created_at", "items", "id", "fee"],
)
