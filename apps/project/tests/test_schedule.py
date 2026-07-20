from datetime import time

import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone

from apps.project.tests.fixtures.data import project_initial_data
from apps.smoothing.choices import ClosedDayChoices
from apps.smoothing.tests.fixtures.data import branch_initial_data

pytestmark = pytest.mark.django_db


class TestScheduleView:
    url = reverse("project:schedules")

    def test_correct(self, api_client, super_user):
        api_client.force_authenticate(user=super_user)
        branch = branch_initial_data.create_object()
        branch.open_time = time(minute=0, hour=0)
        branch.closed_time = time(minute=0, hour=23)
        branch.closed_days = ClosedDayChoices.FRIDAY
        branch.smoothing = super_user.smoothing
        branch.save()

        project = project_initial_data.create_object()
        project.branch = branch
        turn_time = timezone.now()
        project.turn_time = project.turn_time
        project.save()

        response = api_client.get(self.url + f"?month={turn_time.month}&year={turn_time.year}&branch_id={branch.id}")

        times = map(lambda value: value["time"], response.data["result"][10]["times"])
        assert response.status_code == status.HTTP_200_OK
        assert "7:30" not in times
