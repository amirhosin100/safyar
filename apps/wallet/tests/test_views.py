import pytest

from django.urls import reverse
from rest_framework import status

from apps.smoothing.tests.fixtures.data import smoothing_initial_data
from apps.wallet.tests.fixtures.data import wallet_transaction_initial_data

pytestmark = pytest.mark.django_db


class TestWalletTransactionSuperUserListView:
    url = reverse("wallet:owner-transaction-list")

    def test_correct(self, api_client):
        smoothing = smoothing_initial_data.create_object(get_or_create=True)
        smoothing.wallet.transactions.create(
            **wallet_transaction_initial_data.request_data
        )

        response = api_client.get(self.url + "?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_with_normal_user(self, owner_user, api_client):
        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWalletTransactionListView:
    url = reverse("wallet:transaction-list")

    def test_correct(self, api_client, owner_user, super_user):
        owner_user.smoothing.wallet.transactions.create(**wallet_transaction_initial_data.request_data)
        super_user.smoothing.wallet.transactions.create(**wallet_transaction_initial_data.request_data)

        assert owner_user.active_branch is not None
        for user in (owner_user, super_user):
            api_client.force_authenticate(user=user)
            response = api_client.get(self.url + "?page=1")

            assert response.status_code == status.HTTP_200_OK
            assert response.data["count"] == 1

    def test_with_normal_user(self, normal_user, owner_user, api_client, super_user):
        owner_user.smoothing.wallet.transactions.create(**wallet_transaction_initial_data.request_data)
        super_user.smoothing.wallet.transactions.create(**wallet_transaction_initial_data.request_data)

        api_client.force_authenticate(user=normal_user)
        response = api_client.get(self.url + "?page=1")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_with_user_who_joined_branch(self, normal_user, owner_user, api_client, super_user):
        owner_user.smoothing.wallet.transactions.create(**wallet_transaction_initial_data.request_data)
        transcation = super_user.smoothing.wallet.transactions.create(**wallet_transaction_initial_data.request_data)

        normal_user.active_branch = super_user.active_branch
        normal_user.save()

        api_client.force_authenticate(user=normal_user)
        response = api_client.get(self.url + "?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == transcation.id


class TestAddStockWalletView:
    def get_url(self, pk):
        return reverse("wallet:charge-wallet", args=[pk])

    def test_correct(self, api_client, owner_user):
        smoothing = owner_user.smoothing
        url = self.get_url(smoothing.pk)
        wallet_stock = smoothing.wallet.stock

        response = api_client.post(url, {
            "amount": 2000
        })
        smoothing.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert smoothing.wallet.stock == wallet_stock + 2000

    def test_with_normal_user(self, normal_user, api_client, owner_user):
        api_client.force_authenticate(user=normal_user)
        smoothing = owner_user.smoothing
        url = self.get_url(smoothing.pk)
        wallet_stock = smoothing.wallet.stock

        response = api_client.post(url, {
            "amount": 2000
        })
        smoothing.refresh_from_db()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert smoothing.wallet.stock == wallet_stock

    def test_with_anonymous_user(self, api_client, owner_user):
        api_client.force_authenticate(None)
        smoothing = owner_user.smoothing
        url = self.get_url(smoothing.pk)
        wallet_stock = smoothing.wallet.stock

        response = api_client.post(url, {
            "amount": 2000
        })
        smoothing.refresh_from_db()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert smoothing.wallet.stock == wallet_stock