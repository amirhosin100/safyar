# tests/test_login_view.py
import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.choices import UserTypeChoices
from apps.account.models import User, OwnerRequest
from unittest.mock import patch
import uuid

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("account:login")


@pytest.fixture
def active_user():
    """An active user with a known password"""
    user = User.objects.create(
        national_code="3748291650",
        phone_number="09121234567",
        full_name="Test User",
        is_active=True,
    )
    user.set_password("StrongPass@123")
    user.save()
    return user


@pytest.fixture
def inactive_user():
    """An inactive user"""
    user = User.objects.create(
        national_code="6082947315",
        phone_number="09129876543",
        full_name="Inactive User",
        is_active=False,
    )
    user.set_password("StrongPass@123")
    user.save()
    return user


class TestUserLogin:

    def test_login_returns_200(self, api_client, active_user):
        payload = {
            "national_code": active_user.national_code,
            "password": "StrongPass@123",
        }
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data and response.data["access"]
        assert "refresh" in response.data and response.data["refresh"]

    def test_wrong_national_code_returns_404(self, api_client):
        payload = {
            "national_code": "5193047628",
            "password": "StrongPass@123",
        }
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data

    def test_wrong_password_returns_404(self, api_client, active_user):
        payload = {
            "national_code": active_user.national_code,
            "password": "WrongPass@999",
        }
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data
        assert response.data["error"] == "username or password is incorrect"

    def test_inactive_user_returns_404(self, api_client, inactive_user):
        payload = {
            "national_code": inactive_user.national_code,
            "password": "StrongPass@123",
        }
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data
        assert "access" not in response.data

    def test_missing_national_code_returns_400(self, api_client):
        payload = {"password": "StrongPass@123"}
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_password_returns_400(self, api_client):
        payload = {"national_code": "3748291650"}
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_body_returns_400(self, api_client):
        response = api_client.post(LOGIN_URL, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRegisterView:
    url = reverse("account:register")

    @staticmethod
    def _base_data():
        return {
            "full_name": "test name",
            "national_code": "1212880099",
            "phone_number": "09823567890",
            "address": "Yazd",
            "shop_name": "my shop",
            "password1": "StrongPass@123",
            "password2": "StrongPass@123",
        }

    # ── Success ──────────────────────────────────────────────────────────────
    def test_correct(self, api_client):
        response = api_client.post(self.url, self._base_data())

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(national_code="1212880099")
        assert not user.is_active
        assert OwnerRequest.objects.filter(user=user).count() == 1
        assert user.user_type == UserTypeChoices.OWNER

    # ── Duplicate fields ──────────────────────────────────────────────────────
    def test_duplicate_national_code_returns_400(self, api_client):
        """Registering again with the same national code should return 400."""
        User.objects.create(
            national_code="1212880099",
            phone_number="09100000000",
            full_name="existing user",
            is_active=False,
        )
        response = api_client.post(self.url, self._base_data())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_duplicate_phone_number_returns_400(self, api_client):
        """Registering with a duplicate phone number should return 400."""
        User.objects.create(
            national_code="9999999999",
            phone_number="09823567890",  # same number as base_data
            full_name="existing user",
            is_active=False,
        )
        response = api_client.post(self.url, self._base_data())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    # ── Field validation ──────────────────────────────────────────────────────
    def test_password_mismatch_returns_400(self, api_client):
        data = self._base_data()
        data["password2"] = "DifferentPass@999"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_national_code_returns_400(self, api_client):
        """A national code with an invalid format (e.g. fewer than 10 digits) should return 400."""
        data = self._base_data()
        data["national_code"] = "123"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_phone_number_returns_400(self, api_client):
        """A phone number with an invalid format should return 400."""
        data = self._base_data()
        data["phone_number"] = "0912"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_fields_returns_400(self, api_client):
        """Sending an empty payload should return 400."""
        response = api_client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_shop_name_returns_400(self, api_client):
        data = self._base_data()
        data.pop("shop_name")
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ── Method not allowed ────────────────────────────────────────────────────
    def test_get_method_not_allowed(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_not_allowed(self, api_client):
        response = api_client.put(self.url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestResetPasswordView:
    verify_code_url = reverse("account:verify-code")
    reset_password_url = reverse("account:reset-password")
    send_sms_url = reverse("account:send-sms")
    login_url = reverse("account:login")

    def test_correct(self, api_client, normal_user):
        data = {
            "national_code": normal_user.national_code,
        }
        api_client.force_authenticate(user=None)
        with patch("apps.account.views.random.choices") as mocker_choices:
            mocker_choices.return_value = "123456"
            response = api_client.post(self.send_sms_url, data)
            assert response.status_code == status.HTTP_200_OK

        data["code"] = "123456"
        response = api_client.post(
            self.verify_code_url,
            data=data
        )
        assert response.status_code == status.HTTP_200_OK
        response = api_client.post(
            self.login_url,
            data={"national_code": normal_user.national_code, "password": "123456"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        data["password1"] = "123456"
        data["password2"] = "123456"

        response = api_client.post(self.reset_password_url, data)
        assert response.status_code == status.HTTP_200_OK

        assert api_client.post(
            self.login_url,
            data={"national_code": normal_user.national_code, "password": "123456"}
        )
        assert response.status_code == status.HTTP_200_OK

    # TODO write more tests
