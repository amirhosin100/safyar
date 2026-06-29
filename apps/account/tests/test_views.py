# tests/test_login_view.py
import pytest
from django.urls import reverse
from rest_framework import status
from apps.account.models import User

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


@pytest.mark.django_db
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
