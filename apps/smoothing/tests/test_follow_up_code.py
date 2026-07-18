import random
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.choices import FuelTypeChoices, ProjectStatusChoices
from apps.project.models import Project
from apps.smoothing.models import Branch

pytestmark = pytest.mark.django_db


def _create_car_for_branch(branch):
    """Distinct phone_number per call so the same branch can have multiple costumers."""
    car = car_initial_data.create_object()
    car.costumer.phone_number = f"09{random.randint(100000000, 999999999)}"
    car.costumer.branch = branch
    car.costumer.save()
    return car


def _create_project(branch, turn_time=None):
    return Project.objects.create(
        branch=branch,
        car=_create_car_for_branch(branch),
        kilometer_of_car=100,
        fuel_value=FuelTypeChoices.FULL,
        status=ProjectStatusChoices.DELIVERED,
        turn_time=turn_time or timezone.now(),
    )


class TestProjectFollowUpCodeAssignment:
    """`set_code` (pre_save, apps/project/signals.py) sets Project.code from
    Branch.next_follow_up_code and increments it by 1 - only on creation."""

    def test_project_gets_code_from_branch_next_follow_up_code(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 100
        branch.save()

        project = _create_project(branch)

        assert project.code == 100

    def test_branch_next_follow_up_code_increments_after_creation(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 100
        branch.save()

        _create_project(branch)

        branch.refresh_from_db()
        assert branch.next_follow_up_code == 101

    def test_sequential_projects_get_sequential_codes(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 5
        branch.save()

        codes = []
        for i in range(3):
            project = _create_project(branch, turn_time=timezone.now() + timedelta(minutes=i))
            codes.append(project.code)

        assert codes == [5, 6, 7]

    def test_updating_existing_project_does_not_change_code_or_next_follow_up_code(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 10
        branch.save()

        project = _create_project(branch)
        branch.refresh_from_db()
        assert project.code == 10
        assert branch.next_follow_up_code == 11

        project.kilometer_of_car = 200
        project.save()  # update, not create

        branch.refresh_from_db()
        project.refresh_from_db()
        assert project.code == 10
        assert branch.next_follow_up_code == 11


class TestBranchNextFollowUpCodeValidation:
    """`check_codes` (pre_save, apps/smoothing/signals.py) forbids setting
    Branch.next_follow_up_code below the biggest existing Project.code
    for that branch."""

    def test_cannot_set_next_follow_up_code_below_existing_project_code(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 10
        branch.save()

        project = _create_project(branch)  # gets code = 10
        branch.refresh_from_db()  # next_follow_up_code is now 11

        branch.next_follow_up_code = project.code - 1  # 9, less than 10
        with pytest.raises(ValidationError):
            branch.save()

    def test_can_set_next_follow_up_code_equal_to_max_project_code(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 10
        branch.save()

        project = _create_project(branch)
        branch.refresh_from_db()

        branch.next_follow_up_code = project.code
        with pytest.raises(ValidationError):
            branch.save()  # should raise

        branch.refresh_from_db()
        assert branch.next_follow_up_code == 11

    def test_can_increase_next_follow_up_code_above_max_project_code(self, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 10
        branch.save()

        project = _create_project(branch)
        branch.refresh_from_db()

        branch.next_follow_up_code = project.code + 100
        branch.save()

        branch.refresh_from_db()
        assert branch.next_follow_up_code == project.code + 100


    def test_new_branch_creation_skips_validation(self, owner_user):
        """A brand-new branch has no pk yet, so check_codes can't compare against `_pre_next_follow_up_code`."""
        branch = Branch.objects.create(
            smoothing=owner_user.smoothing,
            name="new branch",
            order=2,
            next_follow_up_code=0,
        )
        assert branch.pk is not None

    # ---------------- same rule, through the API ----------------

    def test_api_patch_branch_with_lower_next_follow_up_code_returns_400(self, api_client, owner_user):
        branch = owner_user.active_branch
        branch.next_follow_up_code = 10
        branch.save()

        _create_project(branch)
        branch.refresh_from_db()

        api_client.force_authenticate(owner_user)
        url = reverse("smoothing:branch-smoothing")
        response = api_client.patch(url, data={"next_follow_up_code": 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST