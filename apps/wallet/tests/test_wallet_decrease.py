import datetime
import random

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.core.tests.base_test import BaseTest
from apps.core.wallet.values import (
    SUBMIT_CANCELED_PROJECT,
    SUBMIT_TURNED_PROJECT,
    SUBMIT_ACCEPTED_PROJECT,
    SEND_SINGLE_SMS,
    SEND_BULK_SMS,
)
from apps.costumer.tests.fixtures.data import car_initial_data, costumer_initial_data
from apps.project.choices import ProjectStatusChoices
from apps.project.models import Project
from apps.project.tests.fixtures.data import project_create_data
from apps.wallet.models import Wallet

pytestmark = pytest.mark.django_db


class TestProjectCreationDecreasesWallet:
    urls = BaseTest.get_urls(Project)
    list_create_url = urls[1]

    @staticmethod
    def _set_stock(branch, amount):
        wallet = branch.smoothing.wallet
        wallet.stock = amount
        wallet.save()
        return wallet

    @staticmethod
    def _create_car_for_branch(branch):
        car = car_initial_data.create_object()
        car.costumer.branch = branch
        car.costumer.save()
        return car

    @staticmethod
    def _project_payload(car, branch, status_value):
        data = project_create_data.request_data.copy()
        data["car"] = car.id
        data["branch"] = branch.id
        data["status"] = status_value
        del data["turn_time"]
        if status_value == ProjectStatusChoices.TURNED:
            data["turn_time"] = (timezone.now() + datetime.timedelta(days=1)).replace(minute=0)
        return data

    def test_creating_canceled_project_decreases_wallet_by_correct_amount(self, api_client, owner_user):
        wallet = self._set_stock(owner_user.active_branch, 999999)
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.CANCELED)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        wallet.refresh_from_db()
        assert wallet.stock == 999999 - SUBMIT_CANCELED_PROJECT

    def test_creating_turned_project_decreases_wallet_by_correct_amount(self, api_client, owner_user):
        wallet = self._set_stock(owner_user.active_branch, 999999)
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.TURNED)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        wallet.refresh_from_db()
        assert wallet.stock == 999999 - SUBMIT_TURNED_PROJECT

    def test_creating_submitted_project_decreases_wallet_by_correct_amount(self, api_client, owner_user):
        wallet = self._set_stock(owner_user.active_branch, 999999)
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.SUBMITTED)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        wallet.refresh_from_db()
        assert wallet.stock == 999999 - SUBMIT_ACCEPTED_PROJECT

    def test_creating_project_with_insufficient_wallet_stock_fails_and_does_not_decrease(
            self, api_client, owner_user
    ):
        wallet = self._set_stock(owner_user.active_branch, 500)  # کمتر از هزینه‌ی هر نوع پروژه
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.CANCELED)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        wallet.refresh_from_db()
        assert wallet.stock == 500
        assert not Project.objects.filter(car=car).exists()


class TestSmsSendingDecreasesWallet:

    @staticmethod
    def _set_stock(user, branch, amount):
        from apps.wallet.models import Wallet
        Wallet.objects.filter(smoothing_id=branch.smoothing_id).update(stock=amount)
        # کش‌های FK روی user (smoothing و active_branch) رو پاک می‌کنیم
        # تا هر مسیری که view استفاده کنه (user.smoothing یا
        # user.active_branch.smoothing) یک query تازه از دیتابیس بزنه.
        user.refresh_from_db()

    @staticmethod
    def _create_costumer_for_branch(branch):
        costumer = costumer_initial_data.create_object()
        costumer.branch = branch
        costumer.phone_number = f"09{random.randint(100000000,999999999)}"
        costumer.save()
        return costumer

    def test_single_sms_decreases_wallet_by_correct_amount(self, api_client, owner_user):
        self._set_stock(owner_user, owner_user.active_branch, 999999)
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        url = reverse("smoothing:send-single-sms", args=[costumer.id])
        response = api_client.post(url, data={"message": "hi"})

        assert response.status_code == status.HTTP_200_OK
        wallet = Wallet.objects.get(smoothing=owner_user.active_branch.smoothing_id)
        assert wallet.stock == 999999 - SEND_SINGLE_SMS

    def test_bulk_sms_decreases_wallet_by_correct_amount_per_costumer(self, api_client, owner_user):
        self._set_stock(owner_user, owner_user.active_branch, 999999)
        self._create_costumer_for_branch(owner_user.active_branch)
        self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        url = reverse("smoothing:send-bulk-sms")
        response = api_client.post(url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_200_OK
        wallet = Wallet.objects.get(smoothing_id=owner_user.smoothing_id)
        assert wallet.stock == 999999 - (SEND_BULK_SMS * 2)

    def test_single_sms_with_insufficient_stock_fails_and_does_not_decrease(self, api_client, owner_user):
        self._set_stock(owner_user, owner_user.active_branch, 100)  # کمتر از SEND_SINGLE_SMS
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        url = reverse("smoothing:send-single-sms", args=[costumer.id])
        response = api_client.post(url, data={"message": "hi"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        wallet = Wallet.objects.get(smoothing_id=owner_user.smoothing_id)
        assert wallet.stock == 100

    def test_bulk_sms_with_insufficient_stock_fails_and_does_not_decrease(self, api_client, owner_user):
        self._set_stock(owner_user, owner_user.active_branch, 100)
        self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        url = reverse("smoothing:send-bulk-sms")
        response = api_client.post(url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        wallet = Wallet.objects.get(smoothing_id=owner_user.smoothing_id)
        assert wallet.stock == 100