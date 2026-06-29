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


class TestCreateCaptchaView:
    url = reverse("account:create-captcha")

    def test_correct(self, api_client):
        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_201_CREATED
        assert "captcha_key" in response.data
        assert "captcha_image" in response.data



class TestRegisterView:
    url = reverse("account:register")
    captcha_url = reverse("account:create-captcha")

    def _get_captcha(self, api_client):
        """Creates a real captcha and returns (key, value)."""
        with patch("apps.core.captcha.Captcha._generate_captcha_text") as mock:
            mock.return_value = "11111"
            response = api_client.post(self.captcha_url)
        return response.data["captcha_key"], "11111"

    def _base_data(self, captcha_key, captcha_value):
        return {
            "full_name": "test name",
            "national_code": "1212880099",
            "phone_number": "09823567890",
            "address": "Yazd",
            "shop_name": "my shop",
            "password1": "StrongPass@123",
            "password2": "StrongPass@123",
            "captcha_key": captcha_key,
            "captcha_value": captcha_value,
        }

    # ── Success ──────────────────────────────────────────────────────────────
    def test_correct(self, api_client):
        key, val = self._get_captcha(api_client)
        response = api_client.post(self.url, self._base_data(key, val))

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(national_code="1212880099")
        assert not user.is_active
        assert OwnerRequest.objects.filter(user=user).count() == 1
        assert user.user_type == UserTypeChoices.OWNER

    # ── Captcha ────────────────────────────────────────────────────────────────
    def test_invalid_captcha_value_returns_400(self, api_client):
        """Wrong captcha value should return 400."""
        key, _ = self._get_captcha(api_client)
        data = self._base_data(key, "WRONG")
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["non_field_errors"][0] == 'Your captcha is invalid or expired, please try again.'

    def test_invalid_captcha_key_returns_400(self, api_client):
        """A fake UUID for captcha_key should return 400."""
        data = self._base_data(str(uuid.uuid4()), "11111")
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["non_field_errors"][0] == 'Your captcha is invalid or expired, please try again.'

    def test_missing_captcha_returns_400(self, api_client):
        key, val = self._get_captcha(api_client)
        data = self._base_data(key, val)
        data.pop("captcha_key")
        data.pop("captcha_value")
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "captcha_key" in response.data
        assert "captcha_value" in response.data

    # ── Duplicate fields ──────────────────────────────────────────────────────
    def test_duplicate_national_code_returns_400(self, api_client):
        """Registering again with the same national code should return 400."""
        User.objects.create(
            national_code="1212880099",
            phone_number="09100000000",
            full_name="existing user",
            is_active=False,
        )
        key, val = self._get_captcha(api_client)
        response = api_client.post(self.url, self._base_data(key, val))

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
        key, val = self._get_captcha(api_client)
        response = api_client.post(self.url, self._base_data(key, val))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    # ── Field validation ──────────────────────────────────────────────────────
    def test_password_mismatch_returns_400(self, api_client):
        key, val = self._get_captcha(api_client)
        data = self._base_data(key, val)
        data["password2"] = "DifferentPass@999"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_national_code_returns_400(self, api_client):
        """A national code with an invalid format (e.g. fewer than 10 digits) should return 400."""
        key, val = self._get_captcha(api_client)
        data = self._base_data(key, val)
        data["national_code"] = "123"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_phone_number_returns_400(self, api_client):
        """A phone number with an invalid format should return 400."""
        key, val = self._get_captcha(api_client)
        data = self._base_data(key, val)
        data["phone_number"] = "0912"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_fields_returns_400(self, api_client):
        """Sending an empty payload should return 400."""
        response = api_client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_shop_name_returns_400(self, api_client):
        key, val = self._get_captcha(api_client)
        data = self._base_data(key, val)
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
