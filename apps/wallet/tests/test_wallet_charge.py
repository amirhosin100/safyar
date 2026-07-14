import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestWalletCharge:
    url = reverse("wallet:charge-user-wallet")

    def test_correct(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.url, data={"amount": 100})


        assert response.status_code == status.HTTP_200_OK
