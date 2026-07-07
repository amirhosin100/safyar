import pytest
from rest_framework import status

from apps.core.tests.base_test import BaseTest
from apps.costumer.models import Costumer, Car
from apps.costumer.tests.fixtures.data import (
    costumer_initial_data,
    costumer_create_data,
    car_create_data,
)
from apps.smoothing.tests.fixtures.data import branch_initial_data

pytestmark = pytest.mark.django_db


class TestCostumerView:
    urls = BaseTest.get_urls(Costumer)
    list_create_url = urls[1]

    def detail_url(self, pk):
        urls = BaseTest.get_urls(Costumer)
        return urls[0](pk)

    # ---- helpers -----------------------------------------------------

    @staticmethod
    def _create_costumer_for_branch(branch):
        """Create a Costumer instance bound to the given branch."""
        costumer = costumer_initial_data.create_object()
        costumer.branch = branch
        costumer.save()
        return costumer

    # ---- list ----------------------------------------------------------

    def test_correct_list(self, api_client, owner_user, super_user, admin_user):
        costumer = costumer_initial_data.create_object()
        costumer.smoothing = owner_user.smoothing
        costumer.branch = owner_user.active_branch
        costumer.save()
        admin_user.active_branch = owner_user.smoothing.branches.create(
            name="Admin",
            order=2
        )
        admin_user.allowed_branches.set([])
        admin_user.save()

        #even superuser get nothing
        for user, count in ((owner_user, 1), (super_user, 0), (admin_user, 0)):
            api_client.force_authenticate(user=user)

            response = api_client.get(self.list_create_url)
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == count

    def test_with_super_user(self, api_client, super_user):
        costumer_initial_data.create_object()

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_unauthenticated(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---- create ----------------------------------------------------------

    def test_correct_create(self, api_client, owner_user, super_user):

        for user in (owner_user, super_user):
            costumer_initial_data.request_data["branch"] = user.active_branch.id
            api_client.force_authenticate(user=user)
            response = api_client.post(self.list_create_url, data=costumer_initial_data.request_data)

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["branch"] == user.active_branch.id


    def test_with_unauthorized_branch_and_superuser(self, api_client, super_user, owner_user):
        costumer_initial_data.request_data["branch"] = owner_user.active_branch.id

        api_client.force_authenticate(user=super_user)
        response = api_client.post(self.list_create_url, data=costumer_initial_data.request_data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_unauthenticated(self, client, owner_user):
        data = costumer_create_data.request_data.copy()
        data["branch"] = owner_user.active_branch.id

        response = client.post(self.list_create_url, data=data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_duplicate_phone_number_same_branch(self, api_client, owner_user):
        existing_costumer = self._create_costumer_for_branch(owner_user.active_branch)

        data = costumer_create_data.request_data.copy()
        data["phone_number"] = existing_costumer.phone_number

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {'detail': "phone_number and branch must be unique together"}

    def test_create_same_phone_number_different_branch(self, api_client, owner_user, super_user):
        existing_costumer = self._create_costumer_for_branch(owner_user.active_branch)

        data = costumer_create_data.request_data.copy()
        data["branch"] = super_user.active_branch.id
        data["phone_number"] = existing_costumer.phone_number

        api_client.force_authenticate(user=super_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_invalid_gender_choice(self, api_client, owner_user):
        data = costumer_create_data.request_data.copy()
        data["branch"] = owner_user.active_branch.id
        data["gender"] = "X"

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "gender" in response.data

    def test_create_missing_required_field(self, api_client, owner_user):
        data = costumer_create_data.request_data.copy()
        data["branch"] = owner_user.active_branch.id
        del data["phone_number"]

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone_number" in response.data

    # ---- retrieve ----------------------------------------------------------

    def test_retrieve_success(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.detail_url(costumer.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == costumer.id
        assert response.data["phone_number"] == costumer.phone_number

    def test_retrieve_success_with_super_user(self, api_client, super_user):
        costumer = self._create_costumer_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=super_user)
        response = api_client.get(self.detail_url(costumer.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == costumer.id

    def test_retrieve_not_found_for_other_branch(self, api_client, owner_user, super_user):
        costumer = self._create_costumer_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.detail_url(costumer.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_with_admin_user(self, api_client, admin_user, owner_user):

        del branch_initial_data.request_data["smoothing"]
        branch_1 = owner_user.active_branch
        branch_2 = owner_user.smoothing.branches.create(**branch_initial_data.request_data)
        admin_user.allowed_branches.set([branch_2])
        admin_user.active_branch = branch_2
        admin_user.save()
        api_client.force_authenticate(user=admin_user)

        costumer_1 = self._create_costumer_for_branch(branch_1)
        costumer_2 = self._create_costumer_for_branch(branch_2)

        response = api_client.get(self.detail_url(costumer_1.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response = api_client.get(self.detail_url(costumer_2.id))
        assert response.status_code == status.HTTP_200_OK

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.detail_url(costumer_1.id))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_unauthenticated(self, client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        response = client.get(self.detail_url(costumer.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---- update ----------------------------------------------------------

    def test_update_success(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        data = costumer_create_data.request_data.copy()
        data["branch"] = owner_user.active_branch.id
        data["name"] = "updated name"

        api_client.force_authenticate(user=owner_user)
        response = api_client.put(self.detail_url(costumer.id), data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "updated name"

    def test_partial_update_success(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.detail_url(costumer.id), data={"name": "patched name"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "patched name"

    def test_update_not_found_for_other_branch(self, api_client, owner_user, super_user):
        costumer = self._create_costumer_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.detail_url(costumer.id), data={"name": "hacked name"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_invalid_gender_choice(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.detail_url(costumer.id), data={"gender": "X"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "gender" in response.data

    def test_update_unauthenticated(self, client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        response = client.patch(self.detail_url(costumer.id), data={"name": "x"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_with_admin_user(self, api_client, admin_user, owner_user):

        del branch_initial_data.request_data["smoothing"]
        branch_1 = owner_user.active_branch
        branch_2 = owner_user.smoothing.branches.create(**branch_initial_data.request_data)
        admin_user.allowed_branches.set([branch_2])
        admin_user.active_branch = branch_2
        admin_user.save()
        api_client.force_authenticate(user=admin_user)

        costumer_1 = self._create_costumer_for_branch(branch_1)
        costumer_2 = self._create_costumer_for_branch(branch_2)

        response = api_client.patch(self.detail_url(costumer_1.id), data={"name": "patched name"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response = api_client.patch(self.detail_url(costumer_2.id), data={"name": "patched name"})
        assert response.status_code == status.HTTP_200_OK

        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.detail_url(costumer_1.id))
        assert response.status_code == status.HTTP_200_OK

    # ---- delete ----------------------------------------------------------

    def test_delete_success(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.delete(self.detail_url(costumer.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Costumer.objects.filter(id=costumer.id).exists()

    def test_delete_not_found_for_other_branch(self, api_client, owner_user, super_user):
        costumer = self._create_costumer_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.delete(self.detail_url(costumer.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Costumer.objects.filter(id=costumer.id).exists()

    def test_delete_unauthenticated(self, client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        response = client.delete(self.detail_url(costumer.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Costumer.objects.filter(id=costumer.id).exists()


class TestCarView:
    urls = BaseTest.get_urls(Car)
    list_create_url = urls[1]

    def detail_url(self, pk):
        urls = BaseTest.get_urls(Car)
        return urls[0](pk)

    # ---- helpers -----------------------------------------------------

    @staticmethod
    def _create_costumer_for_branch(branch):
        """Create a Costumer instance bound to the given branch."""
        costumer = costumer_initial_data.create_object()
        costumer.branch = branch
        costumer.save()
        return costumer

    @classmethod
    def _create_car_for_branch(cls, branch):
        """Create a Car instance whose costumer belongs to the given branch."""
        costumer = cls._create_costumer_for_branch(branch)
        return Car.objects.create(
            costumer=costumer,
            plate="11-\u0646-555-45",
            color="red",
        )

    @staticmethod
    def _base_data():
        """Return a fresh copy of car creation payload to avoid shared mutable state."""
        return car_create_data.request_data.copy()

    # ---- list ----------------------------------------------------------

    def test_correct_list(self, api_client, owner_user):
        self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_only_returns_own_branch_cars(self, api_client, owner_user, super_user):
        self._create_car_for_branch(owner_user.active_branch)
        self._create_car_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_unauthenticated(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_user_without_branch(self, api_client, admin_user):
        admin_user.active_branch = None
        admin_user.save()

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ---- create ----------------------------------------------------------

    def test_correct_create(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        data = self._base_data()
        data["costumer"] = costumer.id

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["costumer"] == costumer.id

    def test_create_unauthenticated(self, client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        data = self._base_data()
        data["costumer"] = costumer.id

        response = client.post(self.list_create_url, data=data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_missing_costumer(self, api_client, owner_user):
        data = self._base_data()
        data.pop("costumer", None)

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "costumer" in response.data

    def test_create_invalid_plate(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        data = self._base_data()
        data["costumer"] = costumer.id
        data["plate"] = "invalid-plate"

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "plate" in response.data

    def test_owner_can_create_for_any_branch_in_own_smoothing(self, api_client, owner_user):
        other_branch = owner_user.smoothing.branches.create(name="Second Branch", order=2)
        costumer = self._create_costumer_for_branch(other_branch)
        data = self._base_data()
        data["costumer"] = costumer.id

        api_client.force_authenticate(user=owner_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_cannot_create_for_branch_outside_allowed_branches(
            self, api_client, owner_user, admin_user
    ):
        """
        Admin belongs to the same smoothing but the target branch is not in
        their allowed_branches -> creation must be rejected.
        """
        other_branch = owner_user.smoothing.branches.create(name="Second Branch", order=2)
        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([owner_user.active_branch])
        admin_user.save()

        costumer = self._create_costumer_for_branch(other_branch)
        data = self._base_data()
        data["costumer"] = costumer.id

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Car.objects.filter(costumer=costumer).exists()

    def test_admin_can_create_for_allowed_branch(self, api_client, owner_user, admin_user):
        other_branch = owner_user.smoothing.branches.create(name="Second Branch", order=2)
        admin_user.active_branch = other_branch
        admin_user.allowed_branches.set([other_branch])
        admin_user.save()

        costumer = self._create_costumer_for_branch(other_branch)
        data = self._base_data()
        data["costumer"] = costumer.id

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(self.list_create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED

    # ---- retrieve ----------------------------------------------------------

    def test_retrieve_success(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.detail_url(car.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == car.id

    def test_retrieve_not_found_for_other_branch(self, api_client, owner_user, super_user):
        car = self._create_car_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.detail_url(car.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_unauthenticated(self, client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        response = client.get(self.detail_url(car.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_cannot_retrieve_car_outside_allowed_branches(
            self, api_client, owner_user, admin_user
    ):

        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([])
        admin_user.save()

        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.detail_url(car.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_retrieve_car_in_allowed_branch(self, api_client, owner_user, admin_user):
        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([owner_user.active_branch])
        admin_user.save()

        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.detail_url(car.id))

        assert response.status_code == status.HTTP_200_OK

    # ---- update ----------------------------------------------------------

    def test_update_success(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)
        data = self._base_data()
        data["costumer"] = car.costumer.id
        data["color"] = "blue"

        api_client.force_authenticate(user=owner_user)
        response = api_client.put(self.detail_url(car.id), data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["color"] == "blue"

    def test_partial_update_success(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.detail_url(car.id), data={"color": "green"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["color"] == "green"

    def test_update_not_found_for_other_branch(self, api_client, owner_user, super_user):
        car = self._create_car_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.detail_url(car.id), data={"color": "black"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_unauthenticated(self, client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        response = client.patch(self.detail_url(car.id), data={"color": "black"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_cannot_update_car_outside_allowed_branches(
            self, api_client, owner_user, admin_user
    ):
        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([])
        admin_user.save()

        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(self.detail_url(car.id), data={"color": "black"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        car.refresh_from_db()
        assert car.color != "black"

    def test_admin_can_update_car_active_branch(self, api_client, owner_user, admin_user):
        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([owner_user.active_branch])
        admin_user.active_branch = owner_user.active_branch
        admin_user.save()

        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(self.detail_url(car.id), data={"color": "black"})

        assert response.status_code == status.HTTP_200_OK
        car.refresh_from_db()
        assert car.color == "black"

    # ---- delete ----------------------------------------------------------

    def test_delete_success(self, api_client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.delete(self.detail_url(car.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Car.objects.filter(id=car.id).exists()

    def test_delete_not_found_for_other_branch(self, api_client, owner_user, super_user):
        car = self._create_car_for_branch(super_user.active_branch)

        api_client.force_authenticate(user=owner_user)
        response = api_client.delete(self.detail_url(car.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Car.objects.filter(id=car.id).exists()

    def test_delete_unauthenticated(self, client, owner_user):
        car = self._create_car_for_branch(owner_user.active_branch)

        response = client.delete(self.detail_url(car.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Car.objects.filter(id=car.id).exists()

    def test_admin_cannot_delete_car_outside_allowed_branches(
            self, api_client, owner_user, admin_user
    ):
        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([])
        admin_user.save()

        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(self.detail_url(car.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Car.objects.filter(id=car.id).exists()

    def test_admin_can_delete_car_in_allowed_branch(self, api_client, owner_user, admin_user):
        admin_user.active_branch = owner_user.active_branch
        admin_user.allowed_branches.set([owner_user.active_branch])
        admin_user.save()

        car = self._create_car_for_branch(owner_user.active_branch)

        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(self.detail_url(car.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Car.objects.filter(id=car.id).exists()

