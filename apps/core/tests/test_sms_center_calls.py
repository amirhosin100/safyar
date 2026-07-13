# apps/core/tests/test_sms_center_calls.py
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.models import User
from apps.core.sms import sms_center
from apps.core.sms.messages import (
    CANCELED_PROJECT,
    ACCEPTED_PROJECT,
    TURNED_PROJECT,
    REGISTER_SMS,
    REGISTER_USER_FOR_SUPER_USER,
    SMOOTHING_ACTIVATED,
    SMOOTHING_DEACTIVATED,
)
from apps.core.tests.base_test import BaseTest
from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.choices import ProjectStatusChoices
from apps.project.models import Project
from apps.project.tests.fixtures.data import project_initial_data, project_create_data
from apps.smoothing.models import Smoothing

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

        expected_message = TURNED_PROJECT % str(project.turn_time)
        assert send_mock.call_count == 1
        assert send_mock.call_args[0][0] == car.costumer.phone_number
        assert send_mock.call_args[0][1] == expected_message

    def test_create_delivered_project_does_not_call_any_project_sms(self, api_client, owner_user):
        """DELIVERED در match-case سیگنال وجود نداره، پس هیچ sms_center‌ای صدا زده نمیشه."""
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._project_payload(car, owner_user.active_branch, ProjectStatusChoices.DELIVERED)
        api_client.force_authenticate(owner_user)

        with patch.object(sms_center, "send_canceled_project_sms") as canceled_mock, \
                patch.object(sms_center, "send_accepted_project_sms") as accepted_mock, \
                patch.object(sms_center, "send_turned_project_sms") as turned_mock, \
                patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as send_mock:
            response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
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
