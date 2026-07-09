import pytest
from django.urls import reverse
from rest_framework import status

from apps.conftest import api_client
from apps.core.tests.base_test import BaseTest
from apps.costumer.models import Costumer
from apps.smoothing.models import Smoothing

pytestmark = pytest.mark.django_db


class TestActiveSmoothing:
    example_url = BaseTest.get_urls(Costumer)[1]
    login_url = reverse("account:login")

    @staticmethod
    def smoothing_update_url(pk):
        return BaseTest.get_urls(Smoothing)[0](pk)

    def login_user(self, client, user):
        user.set_password("1234")
        user.save()
        response = client.post(
            self.login_url,
            {
                "national_code": user.national_code,
                "password": "1234",
            }
        )
        access = response.data["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + access)
        return access

    def test_correct(self, client, owner_user):
        self.login_user(client, owner_user)

        response = client.get(self.example_url)
        assert response.status_code == status.HTTP_200_OK

    def test_by_deactivated_smoothing(self, client, owner_user, admin_user, super_user):
        admin_access = self.login_user(client, admin_user)
        owner_access = self.login_user(client, owner_user)
        super_access = self.login_user(client, super_user)

        smoothing = owner_user.smoothing

        response = client.patch(self.smoothing_update_url(smoothing.pk), data={"is_active": False})
        assert response.status_code == status.HTTP_200_OK

        for token, code in (
                (admin_access, 401)
                , (owner_access, 401)
                , (super_access, 200)
        ):
            client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
            response = client.get(self.example_url)
            assert response.status_code == code
            if code == 401:
                assert response.data["detail"] == 'your smoothing is deactivated'

        client.credentials(HTTP_AUTHORIZATION="Bearer " + super_access)
        response = client.patch(self.smoothing_update_url(smoothing.pk), data={"is_active": True})
        assert response.status_code == status.HTTP_200_OK

        client.credentials(HTTP_AUTHORIZATION="Bearer " + admin_access)
        response = client.get(self.example_url)
        assert response.status_code == status.HTTP_200_OK
