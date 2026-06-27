from apps.core.tests.base_test import BaseTestView
from apps.owner.models import Version, UsageMethod


class TestVersionView(BaseTestView):
    model = Version

    def test_with_normal_user(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.list_create_url)
        assert response.status_code == 403

    def test_with_anonymous_user(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == 401


class TestUsageMethodView(BaseTestView):
    model = UsageMethod

    def test_with_normal_user(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.list_create_url)
        assert response.status_code == 403

    def test_with_anonymous_user(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == 401

import pytest
from django.urls import reverse
from rest_framework import status

from apps.owner.models import SupportInformation


SUPPORT_INFO_URL = reverse("owner:owner-support")


@pytest.fixture
def support_info_data():
    return {
        "landline_number": "02112345678",
        "phone_number": "09123456789",
        "email": "support@example.com",
        "accountability_time": "9:00 - 17:00",
    }


@pytest.fixture
def support_info_obj(support_info_data):
    SupportInformation.objects.all().update(**support_info_data)
    return SupportInformation.objects.first()


@pytest.mark.django_db
class TestSupportInformationView:

    # ---------- GET ----------

    def test_get_returns_support_info(self, api_client, support_info_obj):
        response = api_client.get(SUPPORT_INFO_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == support_info_obj.email
        assert response.data["phone_number"] == support_info_obj.phone_number
        assert response.data["landline_number"] == support_info_obj.landline_number
        assert response.data["accountability_time"] == support_info_obj.accountability_time

    def test_get_returns_null_when_no_object_exists(self, api_client):
        response = api_client.get(SUPPORT_INFO_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] is None

    # ---------- PUT ----------

    def test_put_updates_support_info(self, api_client, support_info_obj, support_info_data):
        updated_data = {**support_info_data, "email": "new@example.com"}

        response = api_client.put(SUPPORT_INFO_URL, data=updated_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "new@example.com"
        support_info_obj.refresh_from_db()
        assert support_info_obj.email == "new@example.com"


    # ---------- PATCH ----------

    def test_patch_partially_updates_support_info(self, api_client, support_info_obj):
        response = api_client.patch(SUPPORT_INFO_URL, data={"email": "patched@example.com"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "patched@example.com"
        support_info_obj.refresh_from_db()
        assert support_info_obj.email == "patched@example.com"
        assert support_info_obj.phone_number == support_info_obj.phone_number

    def test_patch_with_invalid_phone_number_returns_400(self, api_client, support_info_obj):
        response = api_client.patch(SUPPORT_INFO_URL, data={"phone_number": "123"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_with_invalid_email_returns_400(self, api_client, support_info_obj):
        response = api_client.patch(SUPPORT_INFO_URL, data={"email": "not-an-email"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ---------- Permissions ----------

    def test_anonymous_user_cannot_access(self, client):
        response = client.get(SUPPORT_INFO_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_normal_user_cannot_access(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(SUPPORT_INFO_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_normal_user_cannot_update(self, api_client, normal_user, support_info_obj):
        api_client.force_authenticate(normal_user)
        response = api_client.patch(SUPPORT_INFO_URL, data={"email": "hack@example.com"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
