import random

import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.models import User
from apps.costumer.models import Costumer, Car
from apps.costumer.tests.fixtures.data import car_initial_data, costumer_initial_data
from apps.project.choices import FuelTypeChoices, ProjectStatusChoices
from apps.project.models import Project
from apps.project.tests.fixtures.data import project_initial_data, project_create_data
from apps.smoothing.choices import JobTypeChoices
from apps.smoothing.models import Colleague, Smoothing
from apps.wallet.choices import TransactionStatusChoices, TransactionTypeChoices
import datetime
from django.utils import timezone
from apps.costumer.choices import GenderChoices

pytestmark = pytest.mark.django_db


# TODO write tests for BranchCostumerReportView and SmoothingBranchReportView
class TestBranchCarCountView:
    url = reverse("report:branch-car-count")

    @staticmethod
    def _create_car_for_branch(branch):
        car = car_initial_data.create_object()
        car.costumer.phone_number = f"09{random.randint(100000000, 999999999)}"
        car.costumer.branch = branch
        car.costumer.save()
        return car

    def test_correct_count(self, api_client, owner_user):
        self._create_car_for_branch(owner_user.active_branch)
        self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["car_count"] == 2

    def test_does_not_count_other_branch_cars(self, api_client, owner_user, super_user):
        self._create_car_for_branch(owner_user.active_branch)
        self._create_car_for_branch(super_user.active_branch)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["car_count"] == 1

    def test_user_without_active_branch_forbidden(self, api_client, admin_user):
        admin_user.active_branch = None
        admin_user.save()
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSmoothingWalletTransactionReportView:
    url = reverse("report:smoothing-transactions")

    @staticmethod
    def _create_transaction(smoothing, transaction_type):
        tracking_code = str(random.randint(1, 1000))
        return smoothing.wallet.transactions.create(
            amount=1000,
            status=TransactionStatusChoices.SUCCESS,
            transaction_type=transaction_type,
            tracking_code=tracking_code,
        )

    def test_correct_counts(self, api_client, owner_user):
        self._create_transaction(owner_user.smoothing, TransactionTypeChoices.SETTLE)
        self._create_transaction(owner_user.smoothing, TransactionTypeChoices.SETTLE)
        self._create_transaction(owner_user.smoothing, TransactionTypeChoices.WITHDRAW)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_transactions"] == 3
        assert response.data["total_settles"] == 2
        assert response.data["total_withdraws"] == 1

    def test_does_not_count_other_smoothing_transactions(self, api_client, owner_user, super_user):
        self._create_transaction(owner_user.smoothing, TransactionTypeChoices.SETTLE)
        self._create_transaction(super_user.smoothing, TransactionTypeChoices.WITHDRAW)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_transactions"] == 1
        assert response.data["total_settles"] == 1
        assert response.data["total_withdraws"] == 0

    def test_admin_user_allowed(self, api_client, admin_user, owner_user):
        self._create_transaction(owner_user.smoothing, TransactionTypeChoices.SETTLE)

        api_client.force_authenticate(admin_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_transactions"] == 1

    def test_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSmoothingUserReportView:
    url = reverse("report:smoothing-users")

    def test_correct_counts(self, api_client, owner_user, admin_user, normal_user):
        normal_user.active_branch = owner_user.active_branch
        normal_user.save()

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        # owner_user + admin_user + normal_user all share owner_user's smoothing
        assert response.data["total_users"] == 3
        assert response.data["total_admin_users"] == 1
        assert response.data["total_normal_users"] == 1

    def test_does_not_count_other_smoothing_users(self, api_client, owner_user, super_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        returned_total = response.data["total_users"]

        assert User.objects.filter(
            active_branch__smoothing=super_user.active_branch.smoothing
        ).count() > 0
        assert returned_total == User.objects.filter(
            active_branch__smoothing=owner_user.active_branch.smoothing
        ).count()

    def test_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBranchColleagueReportView:
    url = reverse("report:branch-colleagues")

    @staticmethod
    def _create_colleague(branch, job_type, name="colleague"):
        return Colleague.objects.create(
            branch=branch,
            name=name,
            phone_number="09120000000",
            job_type=job_type,
        )

    def test_correct_counts(self, api_client, owner_user):
        self._create_colleague(owner_user.active_branch, JobTypeChoices.SMOOTHER)
        self._create_colleague(owner_user.active_branch, JobTypeChoices.PAINTER)
        self._create_colleague(owner_user.active_branch, JobTypeChoices.MASKER, "m1")
        self._create_colleague(owner_user.active_branch, JobTypeChoices.MASKER, "m2")

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_colleagues"] == 4
        assert response.data["total_smoothers"] == 1
        assert response.data["total_painters"] == 1
        assert response.data["total_maskers"] == 2

    def test_does_not_count_other_branch_colleagues(self, api_client, owner_user, super_user):
        self._create_colleague(owner_user.active_branch, JobTypeChoices.SMOOTHER)
        self._create_colleague(super_user.active_branch, JobTypeChoices.PAINTER)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_colleagues"] == 1
        assert response.data["total_painters"] == 0

    def test_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGlobalReportView:
    url = reverse("report:global-report")

    def test_correct(self, api_client, super_user, owner_user, admin_user):
        api_client.force_authenticate(super_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_users"] == User.objects.count()
        assert response.data["total_smoothings"] == Smoothing.objects.count()

    def test_owner_forbidden(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_forbidden(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBranchCostumerReportView:
    url = reverse("report:branch-costumers")

    @staticmethod
    def create_costumers(user, create_two_project=False):
        project = project_initial_data.create_object()
        costumer_1 = project.car.costumer

        p1 = Project.objects.create(
            branch=project.branch,
            car=project.car,
            kilometer_of_car=100,
            fuel_value=FuelTypeChoices.HALF,
            status=ProjectStatusChoices.SUBMITTED
        )

        costumer_initial_data.request_data["phone_number"] = f"0912{random.randint(1000000,9999999)}"
        costumer_2 = Costumer.objects.create(**costumer_initial_data.request_data)

        projects = [p1,project]
        if create_two_project:
            del car_initial_data.request_data["costumer"]
            car = Car.objects.create(**car_initial_data.request_data, costumer=costumer_2)

            p2 = Project.objects.create(
                branch=costumer_2.branch,
                car=car,
                kilometer_of_car=100,
                fuel_value=FuelTypeChoices.HALF,
                status=ProjectStatusChoices.SUBMITTED
            )
            projects.append(p2)

        for costumer in (costumer_1, costumer_2):
            costumer.branch = user.active_branch
            costumer.save()

        for project in projects:
            project.branch = user.active_branch
            project.save()

    # ---- helpers for the tests below ----

    @staticmethod
    def _create_costumer(branch, phone_number=None):
        """Create a Costumer bound to the given branch (distinct phone_number per call)."""
        return Costumer.objects.create(
            branch=branch,
            name="test costumer",
            gender=GenderChoices.MALE,
            phone_number=phone_number or f"09{random.randint(100000000, 999999999)}",
            address="test address",
        )

    @staticmethod
    def _create_car(costumer):
        """Distinct plate per call, so the same costumer can have multiple cars/projects."""
        plate = f"{random.randint(10, 99)}-الف-{random.randint(100, 999)}-{random.randint(10, 99)}"
        return Car.objects.create(costumer=costumer, plate=plate, color="red", name="test car")

    @classmethod
    def _create_project_for_costumer(
            cls, branch, costumer=None, status=ProjectStatusChoices.SUBMITTED, turn_time=None
    ):
        costumer = costumer or cls._create_costumer(branch)
        car = cls._create_car(costumer)
        return Project.objects.create(
            branch=branch,
            car=car,
            kilometer_of_car=100,
            fuel_value=FuelTypeChoices.FULL,
            status=status,
            turn_time=turn_time or timezone.now(),
        )

    @pytest.mark.parametrize("create_two_projects", [True, False])
    def test_correct(self, api_client, owner_user, create_two_projects):
        n = 2 if create_two_projects else 1
        api_client.force_authenticate(owner_user)
        self.create_costumers(owner_user, create_two_projects)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_costumers"] == Costumer.objects.count()
        assert response.data["active_costumers"] == n
        assert response.data["today_submissions"] == 1

    # ---------------- total_costumers ----------------

    def test_total_costumers_only_counts_own_branch(self, api_client, owner_user, super_user):
        self._create_costumer(owner_user.active_branch)
        self._create_costumer(owner_user.active_branch)
        self._create_costumer(super_user.active_branch)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_costumers"] == 2

    def test_total_costumers_zero_when_no_costumers(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_costumers"] == 0

    # ---------------- active_costumers ----------------

    def test_active_costumers_counts_distinct_costumers_only_once(self, api_client, owner_user):
        """A costumer with two projects/cars must still count as 1 active costumer."""
        costumer = self._create_costumer(owner_user.active_branch)
        self._create_project_for_costumer(owner_user.active_branch, costumer, turn_time=timezone.now())
        self._create_project_for_costumer(
            owner_user.active_branch, costumer, turn_time=timezone.now() + datetime.timedelta(hours=1)
        )

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_costumers"] == 1

    def test_active_costumers_ignores_costumers_without_any_project(self, api_client, owner_user):
        self._create_costumer(owner_user.active_branch)  # no project at all

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_costumers"] == 0

    def test_active_costumers_excludes_other_smoothing(self, api_client, owner_user, super_user):
        self._create_project_for_costumer(super_user.active_branch)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_costumers"] == 0

    def test_active_costumers_excludes_branch_not_in_allowed_branches(self, api_client, admin_user, owner_user):
        """
        NOTE: active_costumers is filtered by `allowed_branches`, not `active_branch`.
        A project on a branch of the SAME smoothing that the admin isn't allowed
        to access must not be counted.
        """
        other_branch = owner_user.smoothing.branches.create(name="other branch", order=2)
        self._create_project_for_costumer(other_branch)

        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([owner_user.active_branch])  # other_branch NOT included
        admin_user.save()

        api_client.force_authenticate(admin_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_costumers"] == 0

    def test_active_costumers_includes_other_allowed_branch_in_same_smoothing(self, api_client, owner_user):
        """
        Documents current behavior: unlike total_costumers, active_costumers is NOT
        scoped to `active_branch` only - any project inside the same smoothing whose
        branch is in `allowed_branches` counts too. owner_user's allowed_branches
        auto-include every branch of their own smoothing (see Branch post_save signal).
        """
        other_branch = owner_user.smoothing.branches.create(name="other branch", order=2)
        self._create_project_for_costumer(other_branch)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_costumers"] == 1

    # ---------------- today_submissions ----------------

    def test_today_submissions_counts_only_submitted_status(self, api_client, owner_user):
        self._create_project_for_costumer(owner_user.active_branch, status=ProjectStatusChoices.SUBMITTED)
        self._create_project_for_costumer(
            owner_user.active_branch,
            status=ProjectStatusChoices.CANCELED,
            turn_time=timezone.now() + datetime.timedelta(hours=1),
        )
        self._create_project_for_costumer(
            owner_user.active_branch,
            status=ProjectStatusChoices.DELIVERED,
            turn_time=timezone.now() + datetime.timedelta(hours=2),
        )

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["today_submissions"] == 1

    def test_today_submissions_excludes_other_days(self, api_client, owner_user):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        self._create_project_for_costumer(
            owner_user.active_branch, status=ProjectStatusChoices.SUBMITTED, turn_time=yesterday
        )

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["today_submissions"] == 0

    def test_today_submissions_excludes_other_branch(self, api_client, owner_user, super_user):
        self._create_project_for_costumer(super_user.active_branch, status=ProjectStatusChoices.SUBMITTED)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["today_submissions"] == 0

    def test_today_submissions_counts_multiple_today(self, api_client, owner_user):
        self._create_project_for_costumer(
            owner_user.active_branch, status=ProjectStatusChoices.SUBMITTED, turn_time=timezone.now()
        )
        self._create_project_for_costumer(
            owner_user.active_branch,
            status=ProjectStatusChoices.SUBMITTED,
            turn_time=timezone.now() + datetime.timedelta(hours=1),
        )

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["today_submissions"] == 2

    # ---------------- permissions ----------------

    def test_user_without_active_branch_forbidden(self, api_client, admin_user):
        admin_user.active_branch = None
        admin_user.save()
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_normal_user_is_allowed(self, api_client, normal_user):
        """
        Unlike other report views (which also require IsNotNormalUser),
        BranchCostumerReportView only uses HasBranch - normal users get 200 here.
        """
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_user_is_allowed(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

