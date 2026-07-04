from rest_framework import status

from apps.core.tests.base_test import BaseTestView
from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.models import Project


class TestProjectView(BaseTestView):
    model = Project

    def test_create_with_owner_user(self, api_client, owner_user, admin_user, normal_user):
        car = car_initial_data.create_object()
        for user in (owner_user, admin_user, normal_user):
            api_client.force_authenticate(user=user)
            user.branch = owner_user.branch
            user.branch.save()

            car.costumer.branch = owner_user.branch
            car.costumer.save()

            self.create_data.request_data["car"] = car.id
            response = api_client.post(self.list_create_url, data=self.create_data.request_data)
            assert response.status_code == status.HTTP_201_CREATED

    def test_with_other_users(self, api_client, owner_user, normal_user, super_user):
        car = car_initial_data.create_object()
        car.costumer.branch = owner_user.branch
        car.costumer.save()
        for user, status_code in ((normal_user, 403), (super_user, 201)):
            api_client.force_authenticate(user)

            self.create_data.request_data["car"] = car.id
            response = api_client.post(self.list_create_url, data=self.create_data.request_data)
            assert response.status_code == status_code

    # update
    def test_update_with_allowed_users(self, api_client, owner_user, normal_user, admin_user):
        project = self.initial_data.create_object()

        for user in (owner_user, admin_user, normal_user):
            api_client.force_authenticate(user=user)
            user.branch = owner_user.branch
            user.branch.save()

            self.update_data.request_data["kilometre_of_car"] = 123
            response = api_client.patch(self.detail_update_delete_url(project.pk), data=self.update_data.request_data)
            project.refresh_from_db()
            assert response.status_code == status.HTTP_200_OK
            assert project.kilometre_of_car == 123

            project.kilometer_of_car = 10
            project.save()
