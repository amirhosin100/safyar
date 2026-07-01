import pytest
from rest_framework import status

from apps.core.tests.base_test import BaseTest
from apps.costumer.models import Costumer, Car
from apps.costumer.tests.fixtures.data import costumer_initial_data, car_initial_data, car_create_data

pytestmark = pytest.mark.django_db


class TestCostumerView:
    urls = BaseTest.get_urls(Costumer)
    detail_url = urls[0]
    list_create_url = urls[1]

    def test_correct_list(self, api_client, owner_user, super_user):
        costumer = costumer_initial_data.create_object()
        owner_user.branch = costumer.branch
        owner_user.save()

        for user, count in ((owner_user, 1), (super_user, 0)):
            api_client.force_authenticate(user=user)

            response = api_client.get(self.list_create_url)
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == count

    def test_correct_create(self, api_client, owner_user, super_user):
        del costumer_initial_data.request_data["branch"]

        for user in (owner_user, super_user):
            api_client.force_authenticate(user=user)
            response = api_client.post(self.list_create_url, data=costumer_initial_data.request_data)

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["branch"] == user.branch.id

    # TODO write more tests


class TestCarView:
    urls = BaseTest.get_urls(Car)
    detail_url = urls[0]
    list_create_url = urls[1]

    def test_correct_list(self, api_client, owner_user, super_user):
        car = car_initial_data.create_object(get_or_create=True)

    def test_create(self, api_client, super_user):
        car_create_data.set_up()
        costumer = Costumer.objects.first()
        costumer.branch = super_user.branch
        costumer.save()
        response = api_client.post(
            self.list_create_url,
            data=car_create_data.request_data,
        )
        assert response.status_code == status.HTTP_201_CREATED
        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
