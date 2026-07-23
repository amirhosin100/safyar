# apps/core/tests/test_sms_center_calls.py
import datetime
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.models import User
from apps.core.sms import sms_center
from apps.core.tests.base_test import BaseTest
from apps.core.utils.time import to_persian_date
from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.models import Project
from apps.project.tests.fixtures.data import project_initial_data, project_create_data
from apps.smoothing.models import Smoothing
from django.utils import timezone
from apps.project.choices import ProjectStatusChoices, FuelTypeChoices
from django.conf import settings

from apps.core.sms.messages import (
    CANCELED_PROJECT,
    ACCEPTED_PROJECT,
    TURNED_PROJECT,
    REGISTER_SMS,
    REGISTER_USER_FOR_SUPER_USER,
    SMOOTHING_ACTIVATED,
    SMOOTHING_DEACTIVATED,
    WALLET_STOCK_WARN,
    WALLET_STOCK_EMPTY,
)
from apps.core.wallet.values import SEND_SINGLE_SMS
from apps.costumer.tests.fixtures.data import costumer_initial_data

pytestmark = pytest.mark.django_db


class TestProjectSmsCenterCalls:
    urls = BaseTest.get_urls(Project)
    list_create_url = urls[1]

    def detail_url(self, pk):
        return self.urls[0](pk)

    @staticmethod
    def _add_stock(branch):
        branch.smoothing.wallet.stock = 999999
        branch.smoothing.wallet.save()

    def _create_car_for_branch(self, branch):
        # add stock
        self._add_stock(branch)
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

    def test_create_canceled_project_calls_send_canceled_project_sms(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.CANCELED)
        api_client.force_authenticate(owner_user)

        with patch.object(
                sms_center, "send_canceled_project_sms", wraps=sms_center.send_canceled_project_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert center_mock.call_count == 1
        assert center_mock.call_args[0][0].id == response.data["id"]

        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == car.costumer.phone_number
        assert send_mock.call_args[0][1] == CANCELED_PROJECT

    def test_create_submitted_project_calls_send_accepted_project_sms(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.SUBMITTED)
        api_client.force_authenticate(owner_user)

        with patch.object(
                sms_center, "send_accepted_project_sms", wraps=sms_center.send_accepted_project_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert center_mock.call_count == 1
        assert center_mock.call_args[0][0].id == response.data["id"]

        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == car.costumer.phone_number
        assert send_mock.call_args[0][1] == ACCEPTED_PROJECT

    def test_create_turned_project_calls_send_turned_project_sms(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.TURNED)
        api_client.force_authenticate(owner_user)

        with patch.object(
                sms_center, "send_turned_project_sms", wraps=sms_center.send_turned_project_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert center_mock.call_count == 1
        project = Project.objects.get(pk=response.data["id"])
        assert center_mock.call_args[0][0].id == project.id

        # a fresh DB fetch normalizes turn_time to UTC; localize it back so it
        # matches what the signal saw in-memory (original +03:30 offset)
        time = timezone.localtime(project.turn_time)
        time = to_persian_date(time)
        expected_message = TURNED_PROJECT % str(time)
        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == car.costumer.phone_number
        assert send_mock.call_args[0][1] == expected_message

    def test_create_delivered_project_does_not_call_any_project_sms(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        with patch.object(sms_center, "send_canceled_project_sms") as canceled_mock, \
                patch.object(sms_center, "send_accepted_project_sms") as accepted_mock, \
                patch.object(sms_center, "send_turned_project_sms") as turned_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            Project.objects.create(
                branch=owner_user.active_branch,
                car=car,
                kilometer_of_car=300,
                fuel_value=FuelTypeChoices.FULL,
                status=ProjectStatusChoices.DELIVERED,
            )

        assert canceled_mock.call_count == 0
        assert accepted_mock.call_count == 0
        assert turned_mock.call_count == 0
        assert send_mock.call_count == 0

    def test_update_does_not_trigger_project_sms(self, api_client, owner_user):
        """سیگنال فقط با created=True فایر میشه، پس آپدیت نباید پیامکی بفرسته."""
        project = project_initial_data.create_object()
        project.branch = owner_user.active_branch
        project.save()
        api_client.force_authenticate(owner_user)

        with patch.object(sms_center, "send_turned_project_sms") as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 999})

        assert response.status_code == status.HTTP_200_OK
        assert center_mock.call_count == 0
        assert send_mock.call_count == 0


class TestRegisterSmsCenterCalls:
    url = reverse("account:register")

    @staticmethod
    def _payload(national_code, phone_number):
        return {
            "full_name": "test name",
            "national_code": national_code,
            "phone_number": phone_number,
            "address": "Yazd",
            "shop_name": "my shop",
            "password1": "StrongPass@123",
            "password2": "StrongPass@123",
        }

    def test_register_without_super_user_calls_send_register_sms_only(self, client):
        data = self._payload("1212880099", "09823567890")

        with patch.object(
                sms_center, "send_register_sms", wraps=sms_center.send_register_sms
        ) as register_center_mock, \
                patch.object(sms_center, "send_register_smoothing_for_super_user") as super_center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED
        registered_user = User.objects.get(national_code="1212880099")

        assert register_center_mock.call_count == 1
        assert register_center_mock.call_args[0][0] == registered_user
        assert super_center_mock.call_count == 0

        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == registered_user.phone_number
        assert send_mock.call_args[0][1] == REGISTER_SMS

    def test_register_with_super_user_calls_send_register_smoothing_for_super_user(self, client, super_user):
        data = self._payload("1212880098", "09823567891")

        with patch.object(
                sms_center, "send_register_sms", wraps=sms_center.send_register_sms
        ) as register_center_mock, \
                patch.object(
                    sms_center,
                    "send_register_smoothing_for_super_user",
                    wraps=sms_center.send_register_smoothing_for_super_user,
                ) as super_center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED
        registered_user = User.objects.get(national_code="1212880098")

        assert register_center_mock.call_count == 1
        assert super_center_mock.call_count == 1
        assert super_center_mock.call_args[0] == (registered_user, super_user)

        # send_single_sms باید دوبار صدا زده بشه: یکبار برای ثبت‌نام کاربر، یکبار برای اطلاع به super_user
        assert send_mock.call_count == 2
        called_phones = {call.args[0] for call in send_mock.call_args_list}
        assert called_phones == {registered_user.phone_number, super_user.phone_number}

        super_user_call = next(
            call for call in send_mock.call_args_list if call.args[0] == super_user.phone_number
        )
        assert super_user_call.args[1] == REGISTER_USER_FOR_SUPER_USER % registered_user.full_name


class TestSmoothingActivationSmsCenterCalls:

    def detail_url(self, pk):
        return BaseTest.get_urls(Smoothing)[0](pk)

    def test_deactivating_smoothing_calls_send_smoothing_deactivated_sms(self, api_client, owner_user):
        with patch.object(
                sms_center, "send_smoothing_deactivated_sms", wraps=sms_center.send_smoothing_deactivated_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.patch(self.detail_url(owner_user.smoothing.pk), data={"is_active": False})

        assert response.status_code == status.HTTP_200_OK
        assert center_mock.call_count == 1
        assert center_mock.call_args[0][0] == owner_user

        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == owner_user.phone_number
        assert send_mock.call_args[0][1] == SMOOTHING_DEACTIVATED

    def test_activating_smoothing_calls_send_smoothing_activated_sms(self, api_client, owner_user):
        owner_user.smoothing.is_active = False
        owner_user.smoothing.save()

        with patch.object(
                sms_center, "send_smoothing_activated_sms", wraps=sms_center.send_smoothing_activated_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.patch(self.detail_url(owner_user.smoothing.pk), data={"is_active": True})

        assert response.status_code == status.HTTP_200_OK
        assert center_mock.call_count == 1
        assert center_mock.call_args[0][0] == owner_user

        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == owner_user.phone_number
        assert send_mock.call_args[0][1] == SMOOTHING_ACTIVATED

    def test_updating_unrelated_field_does_not_trigger_activation_sms(self, api_client, owner_user):
        with patch.object(sms_center, "send_smoothing_deactivated_sms") as deactivated_mock, \
                patch.object(sms_center, "send_smoothing_activated_sms") as activated_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.patch(self.detail_url(owner_user.smoothing.pk), data={"name": "renamed shop"})

        assert response.status_code == status.HTTP_200_OK
        assert deactivated_mock.call_count == 0
        assert activated_mock.call_count == 0
        assert send_mock.call_count == 0


class TestWalletSmsCenterCalls:

    @staticmethod
    def _create_costumer_for_branch(branch):
        costumer = costumer_initial_data.create_object()
        costumer.branch = branch
        costumer.save()
        return costumer

    @staticmethod
    def _single_sms_url(costumer_id):
        return reverse("smoothing:send-single-sms", args=[costumer_id])

    @staticmethod
    def _charge_wallet_via_api(api_client, super_user, smoothing_id, amount):
        api_client.force_authenticate(super_user)
        url = reverse("wallet:charge-wallet", args=[smoothing_id])
        response = api_client.post(url, {"amount": amount})
        assert response.status_code == status.HTTP_200_OK

    # ---------------- warning ----------------

    def test_wallet_warning_sms_sent_when_stock_crosses_below_warning_threshold(
            self, api_client, owner_user, super_user
    ):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        wallet = owner_user.smoothing.wallet

        target_stock_after_decrease = settings.WALLET_WARNING_STOCK - 1  # 99999
        self._charge_wallet_via_api(
            api_client, super_user, owner_user.smoothing.pk,
            amount=target_stock_after_decrease + SEND_SINGLE_SMS,
        )

        api_client.force_authenticate(owner_user)

        with patch.object(
                sms_center, "send_wallet_stock_waring_sms", wraps=sms_center.send_wallet_stock_waring_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.post(self._single_sms_url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_200_OK

        wallet.refresh_from_db()
        assert wallet.stock == target_stock_after_decrease
        assert wallet.is_sent_warning_sms is True

        assert center_mock.call_count == 1
        assert center_mock.call_args[0][0] == wallet

        assert send_mock.call_count == 2
        warning_call = next(
            call for call in send_mock.call_args_list if call.args[0] == owner_user.phone_number
        )
        assert warning_call.args[1] == WALLET_STOCK_WARN % wallet.stock

    def test_wallet_warning_sms_not_sent_again_once_already_flagged(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        wallet = owner_user.smoothing.wallet
        wallet.stock = settings.WALLET_WARNING_STOCK - 1
        wallet.is_sent_warning_sms = True
        wallet.save()

        api_client.force_authenticate(owner_user)

        with patch.object(sms_center, "send_wallet_stock_waring_sms") as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True):
            response = api_client.post(self._single_sms_url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_200_OK
        assert center_mock.call_count == 0

    # ---------------- empty ----------------

    def test_wallet_empty_sms_sent_when_stock_crosses_below_empty_threshold(
            self, api_client, owner_user, super_user
    ):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        wallet = owner_user.smoothing.wallet

        target_stock_after_decrease = settings.WALLET_EMPTY_STOCK - 1  # 999
        self._charge_wallet_via_api(
            api_client, super_user, owner_user.smoothing.pk,
            amount=target_stock_after_decrease + SEND_SINGLE_SMS,
        )

        api_client.force_authenticate(owner_user)

        with patch.object(
                sms_center, "send_wallet_stock_empty_sms", wraps=sms_center.send_wallet_stock_empty_sms
        ) as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.post(self._single_sms_url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_200_OK

        wallet.refresh_from_db()
        assert wallet.stock == target_stock_after_decrease
        assert wallet.is_sent_empty_sms is True

        assert center_mock.call_count == 1
        assert center_mock.call_args[0][0] == wallet

        assert send_mock.call_count == 2
        empty_call = next(
            call for call in send_mock.call_args_list if call.args[0] == owner_user.phone_number
        )
        assert empty_call.args[1] == WALLET_STOCK_EMPTY

    def test_wallet_empty_sms_not_sent_again_once_already_flagged(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        wallet = owner_user.smoothing.wallet
        wallet.stock = settings.WALLET_EMPTY_STOCK - 1
        wallet.is_sent_empty_sms = True
        wallet.save()

        api_client.force_authenticate(owner_user)

        with patch.object(sms_center, "send_wallet_stock_empty_sms") as center_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True):
            response = api_client.post(self._single_sms_url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert center_mock.call_count == 0
