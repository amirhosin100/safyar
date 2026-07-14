import random

import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.models import User
from apps.costumer.tests.fixtures.data import car_initial_data
from apps.smoothing.choices import JobTypeChoices
from apps.smoothing.models import Colleague, Smoothing
from apps.wallet.choices import TransactionStatusChoices, TransactionTypeChoices

pytestmark = pytest.mark.django_db

#TODO write tests for BranchCostumerReportView and SmoothingBranchReportView
class TestBranchCarCountView:
    url = reverse("report:branch-car-count")

    @staticmethod
    def _create_car_for_branch(branch):
        car = car_initial_data.create_object()
        car.costumer.phone_number = f"09{random.randint(100000000,999999999)}"
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
        return smoothing.wallet.transactions.create(
            amount=1000,
            status=TransactionStatusChoices.SUCCESS,
            transaction_type=transaction_type,
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
