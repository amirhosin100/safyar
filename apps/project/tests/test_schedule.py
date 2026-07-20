import datetime
import random

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.choices import FuelTypeChoices, ProjectStatusChoices
from apps.project.models import Project
from apps.smoothing.choices import ClosedDayChoices

pytestmark = pytest.mark.django_db


class TestProjectScheduleListView:
    url = reverse("project:schedules")

    # ---------------- helpers ----------------

    @staticmethod
    def _set_branch_hours(
        branch,
        open_time=datetime.time(0, 0),
        closed_time=datetime.time(23, 30),
        closed_days=ClosedDayChoices.NO_DAYS_OFF,
    ):
        branch.open_time = open_time
        branch.closed_time = closed_time
        branch.closed_days = closed_days
        branch.save()
        return branch

    @staticmethod
    def _create_car_for_branch(branch):
        """Distinct phone_number per call so multiple cars can share a branch."""
        car = car_initial_data.create_object()
        car.costumer.phone_number = f"09{random.randint(100000000, 999999999)}"
        car.costumer.branch = branch
        car.costumer.save()
        return car

    def _create_project(self, branch, turn_time):
        return Project.objects.create(
            branch=branch,
            car=self._create_car_for_branch(branch),
            kilometer_of_car=100,
            fuel_value=FuelTypeChoices.FULL,
            status=ProjectStatusChoices.DELIVERED,
            turn_time=turn_time,
        )

    def _call(self, api_client, branch, year, month):
        return api_client.get(self.url, {"year": year, "month": month, "branch_id": branch.id})

    @staticmethod
    def _find_day(result, date_str):
        return next((day for day in result if day["date"] == date_str), None)

    @staticmethod
    def _weekday_of(date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").weekday()

    # ---------------- basic structure ----------------

    def test_correct_structure(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(owner_user.active_branch)
        now = timezone.localtime()

        response = self._call(api_client, branch, now.year, now.month)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["open_time"] == branch.open_time
        assert response.data["close_time"] == branch.closed_time
        assert isinstance(response.data["result"], list)
        # every day of the month must appear, even the ones with empty times
        assert len(response.data["result"]) > 27

    # ---------------- past-time exclusion ----------------

    def test_past_times_of_today_are_excluded(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(owner_user.active_branch)
        now = timezone.localtime()

        response = self._call(api_client, branch, now.year, now.month)
        today_entry = self._find_day(response.data["result"], now.strftime("%Y-%m-%d"))

        assert today_entry is not None
        current_time_str = now.strftime("%H:%M")
        for slot in today_entry["times"]:
            assert slot["time"] >= current_time_str

    def test_future_day_is_not_affected_by_past_time_filter(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(owner_user.active_branch)
        now = timezone.localtime()
        target = now + datetime.timedelta(days=1)
        if target.month != now.month:  # avoid crossing into next month
            target = now - datetime.timedelta(days=1)

        response = self._call(api_client, branch, now.year, now.month)
        entry = self._find_day(response.data["result"], target.strftime("%Y-%m-%d"))

        assert entry is not None
        # a day other than "today" must include the opening slot
        assert any(slot["time"] == "00:00" for slot in entry["times"])

    # ---------------- closed days ----------------

    def test_closed_day_has_empty_times_but_key_present(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(owner_user.active_branch, closed_days=ClosedDayChoices.FRIDAY)
        now = timezone.localtime()

        response = self._call(api_client, branch, now.year, now.month)

        friday_entries = [day for day in response.data["result"] if self._weekday_of(day["date"]) == 4]
        assert friday_entries, "there should be at least one Friday in this month"
        for entry in friday_entries:
            assert entry["times"] == []

    # ---------------- already booked slots ----------------

    def test_booked_time_is_removed_from_available_times(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(owner_user.active_branch)
        now = timezone.localtime()
        target = now + datetime.timedelta(days=2)
        if target.month != now.month:
            target = now - datetime.timedelta(days=2)

        turn_time = target.replace(hour=10, minute=0, second=0, microsecond=0)
        self._create_project(branch, turn_time)

        response = self._call(api_client, branch, now.year, now.month)
        entry = self._find_day(response.data["result"], target.strftime("%Y-%m-%d"))

        assert entry is not None
        assert not any(slot["time"] == "10:00" for slot in entry["times"])
        # a neighboring slot must still be free
        assert any(slot["time"] == "10:30" for slot in entry["times"])

    # ---------------- validation ----------------

    def test_missing_params_returns_400(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_month_returns_400(self, api_client):
        response = api_client.get(self.url, {"year": "2026", "month": "13", "branch_id": 1})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_year_returns_400(self, api_client):
        response = api_client.get(self.url, {"year": "26", "month": "7", "branch_id": 1})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_branch_not_found_returns_400(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url, {"year": "2026", "month": "7", "branch_id": 999999})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ---------------- permissions ----------------

    def test_unauthenticated_returns_401(self, client, owner_user):
        response = client.get(
            self.url,
            {"year": "2026", "month": "7", "branch_id": owner_user.active_branch.id},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_owner_can_view_own_branch_schedule(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(owner_user.active_branch)
        response = self._call(api_client, branch, 2026, 7)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_without_allowed_branch_forbidden(self, api_client, admin_user):
        branch = self._set_branch_hours(admin_user.active_branch)
        response = self._call(api_client, branch, 2026, 7)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_with_allowed_branch_ok(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        branch = self._set_branch_hours(admin_user.active_branch)
        admin_user.allowed_branches.add(branch)
        response = self._call(api_client, branch, 2026, 7)
        assert response.status_code == status.HTTP_200_OK

    def test_cross_smoothing_branch_forbidden_for_owner(self, api_client, owner_user, super_user):
        api_client.force_authenticate(owner_user)
        branch = self._set_branch_hours(super_user.active_branch)
        response = self._call(api_client, branch, 2026, 7)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_without_active_branch_forbidden(self, api_client, admin_user,owner_user):
        api_client.force_authenticate(admin_user)
        admin_user.active_branch = None
        admin_user.save()
        response = api_client.get(self.url, {"year": "2026", "month": "7", "branch_id": owner_user.active_branch.id})
        assert response.status_code == status.HTTP_403_FORBIDDEN
