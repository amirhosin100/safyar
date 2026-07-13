import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.core.tests.base_test import BaseTestModel
from apps.core.tests.image import create_image
from apps.costumer.tests.fixtures.data import car_initial_data
from apps.project.choices import FuelTypeChoices, FixTypeChoices, TemporalChoices
from apps.project.models import Project, ProjectImage, FixItem, MainPart, FixArea
from apps.project.tests.fixtures.data import project_initial_data
from apps.smoothing.tests.fixtures.data import branch_initial_data

pytestmark = pytest.mark.django_db


class TestMainPartView:
    url = reverse("project:main-parts")

    def test_correct(self,api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "areas" in response.data[0]



class TestProjectView(BaseTestModel):
    model = Project

    def test_create_with_owner_user(self, api_client, owner_user, admin_user, normal_user):
        car = car_initial_data.create_object()
        for user in (owner_user, admin_user, normal_user):
            api_client.force_authenticate(user=user)
            user.active_branch = owner_user.active_branch
            user.active_branch.save()

            car.costumer.branch = owner_user.active_branch
            car.costumer.save()

            self.create_data.request_data["car"] = car.id
            self.create_data.request_data["branch"] = car.branch.id

            response = api_client.post(self.list_create_url, data=self.create_data.request_data)
            assert response.status_code == status.HTTP_201_CREATED
            Project.objects.filter(pk=response.data["id"]).delete()

    def test_with_other_users(self, api_client, owner_user, normal_user, super_user):
        car = car_initial_data.create_object()
        car.costumer.branch = owner_user.active_branch
        car.costumer.save()
        for user, status_code in ((normal_user, 403), (super_user, 201)):
            api_client.force_authenticate(user)

            self.create_data.request_data["car"] = car.id
            self.create_data.request_data["branch"] = car.branch.id
            response = api_client.post(self.list_create_url, data=self.create_data.request_data)
            assert response.status_code == status_code

    # update

    def test_update_with_allowed_users(self, api_client, owner_user, normal_user, admin_user):
        project = self.initial_data.create_object()

        for user in (owner_user, admin_user, normal_user):
            user.active_branch = owner_user.active_branch
            user.allowed_branches.set([owner_user.active_branch])
            user.save()

            project.branch = user.active_branch
            project.save()

            api_client.force_authenticate(user=user)

            self.update_data.request_data["kilometer_of_car"] = 123
            self.update_data.request_data["branch"] = project.branch.id
            response = api_client.patch(self.detail_update_delete_url(project.pk), data=self.update_data.request_data)
            project.refresh_from_db()
            assert response.status_code == status.HTTP_200_OK
            assert project.kilometer_of_car == 123

            project.kilometer_of_car = 10
            project.save()


class TestProjectViewPermissions:
    urls = BaseTestModel.get_urls(Project)
    list_create_url = urls[1]

    def detail_url(self, pk):
        return self.urls[0](pk)

    @staticmethod
    def _create_project_for_branch(branch):
        project = project_initial_data.create_object()
        project.branch = branch
        project.branch.open_time = branch_initial_data.request_data["open_time"]
        project.branch.closed_time = branch_initial_data.request_data["closed_time"]
        project.branch.save()
        project.save()  # Project.save() derives smoothing from branch automatically
        return project

    # ---------------- retrieve ----------------

    def test_retrieve_owner_with_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_owner_without_allowed_branch_not_found(self, api_client, owner_user):
        """
        Even the owner of the smoothing is blocked once the branch is removed
        from their allowed_branches - there is no smoothing-only fallback.
        """
        project = self._create_project_for_branch(owner_user.active_branch)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_super_user_without_allowed_branch_not_found(self, api_client, super_user):
        """Same rule applies to SUPER_USER - allowed_branches is required regardless of type."""
        project = self._create_project_for_branch(super_user.active_branch)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_admin_without_allowed_branch_not_found(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        # admin_user.allowed_branches is empty by default
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_normal_user_with_allowed_branch(self, api_client, normal_user, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        normal_user.active_branch = owner_user.active_branch
        normal_user.allowed_branches.set([owner_user.active_branch])
        normal_user.save()

        api_client.force_authenticate(normal_user)
        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_normal_user_without_allowed_branch_not_found(self, api_client, normal_user, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        normal_user.active_branch = owner_user.active_branch
        normal_user.save()
        # allowed_branches intentionally left empty

        api_client.force_authenticate(normal_user)
        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_cross_smoothing_not_found(self, api_client, owner_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_user_without_active_branch_forbidden(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        admin_user.active_branch = None
        admin_user.save()

        api_client.force_authenticate(admin_user)
        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_unauthenticated(self, client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        response = client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---------------- update ----------------

    def test_update_requires_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 555})
        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.kilometer_of_car == 555

    def test_update_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 555})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_super_user_without_allowed_branch_not_found(self, api_client, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 555})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 777})
        assert response.status_code == status.HTTP_200_OK

    def test_update_admin_without_allowed_branch_not_found(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 777})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_cross_smoothing_not_found(self, api_client, owner_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 1})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ---------------- delete ----------------

    def test_delete_requires_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(pk=project.pk).exists()

    def test_delete_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Project.objects.filter(pk=project.pk).exists()

    def test_delete_super_user_without_allowed_branch_not_found(self, api_client, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.delete(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Project.objects.filter(pk=project.pk).exists()

    def test_delete_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.delete(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_admin_without_allowed_branch_not_found(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.delete(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Project.objects.filter(pk=project.pk).exists()

    # ---------------- list ----------------

    def test_list_returns_only_allowed_branches_projects(self, api_client, owner_user, super_user):
        own_project = self._create_project_for_branch(owner_user.active_branch)
        other_project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {p["id"] for p in response.data}
        assert own_project.pk in returned_ids
        assert other_project.pk not in returned_ids

    def test_list_owner_without_allowed_branch_sees_nothing(self, api_client, owner_user):
        """
        List filtering relies on the same two conditions as detail/update/
        delete, so even the owner sees nothing for a branch once it's
        removed from their allowed_branches.
        """
        self._create_project_for_branch(owner_user.active_branch)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_admin_sees_all_allowed_branches(self, api_client, admin_user, owner_user):
        branch_2 = owner_user.smoothing.branches.create(name="second branch", order=2)
        admin_user.allowed_branches.set([admin_user.active_branch, branch_2])
        api_client.force_authenticate(admin_user)

        project_1 = self._create_project_for_branch(admin_user.active_branch)
        project_2 = self._create_project_for_branch(branch_2)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        returned_ids = {p["id"] for p in response.data}
        assert project_1.pk in returned_ids
        assert project_2.pk in returned_ids

    def test_list_normal_user_only_sees_allowed_branches(self, api_client, normal_user, owner_user):
        allowed_project = self._create_project_for_branch(owner_user.active_branch)
        not_allowed_project = self._create_project_for_branch(normal_user.active_branch)

        normal_user.active_branch = owner_user.active_branch
        normal_user.allowed_branches.set([owner_user.active_branch])
        normal_user.save()

        api_client.force_authenticate(normal_user)
        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {p["id"] for p in response.data}
        assert allowed_project.pk in returned_ids
        assert not_allowed_project.pk not in returned_ids

    def test_list_unauthenticated(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_user_without_active_branch_forbidden(self, api_client, admin_user):
        admin_user.active_branch = None
        admin_user.save()
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectViewCrossSmoothingAccess:
    """
    Regression coverage for the smoothing isolation fix: get_queryset() now
    filters by BOTH allowed_branches AND smoothing=active_branch.smoothing,
    so cross-smoothing access is denied even in the edge case where a
    foreign branch ends up in a user's allowed_branches.
    """

    urls = BaseTestModel.get_urls(Project)
    list_create_url = urls[1]

    def detail_url(self, pk):
        return self.urls[0](pk)

    @staticmethod
    def _create_project_for_branch(branch):
        project = project_initial_data.create_object()
        project.branch = branch
        project.save()
        return project

    def test_admin_from_other_smoothing_cannot_retrieve(self, api_client, admin_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_normal_user_from_other_smoothing_cannot_retrieve(self, api_client, normal_user, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        api_client.force_authenticate(normal_user)

        response = api_client.get(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_from_other_smoothing_cannot_update(self, api_client, admin_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.patch(self.detail_url(project.pk), data={"kilometer_of_car": 1})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_from_other_smoothing_cannot_delete(self, api_client, admin_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.delete(self.detail_url(project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Project.objects.filter(pk=project.pk).exists()

    def test_admin_from_other_smoothing_list_does_not_include_it(self, api_client, admin_user, super_user):
        other_project = self._create_project_for_branch(super_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        returned_ids = {p["id"] for p in response.data}
        assert other_project.pk not in returned_ids

    def test_access_denied_even_if_foreign_branch_is_in_allowed_branches(
            self, api_client, normal_user, owner_user
    ):
        """
        Even if a branch belonging to a completely different smoothing
        somehow ends up in a user's allowed_branches, the smoothing filter
        in get_queryset() still blocks access, since the project's smoothing
        does not match the user's own active_branch.smoothing.
        """
        foreign_project = self._create_project_for_branch(owner_user.active_branch)

        # Deliberately grant access to a branch from a different smoothing
        normal_user.allowed_branches.add(owner_user.active_branch)
        api_client.force_authenticate(normal_user)

        response = api_client.get(self.detail_url(foreign_project.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = api_client.patch(
            self.detail_url(foreign_project.pk), data={"kilometer_of_car": 42}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        returned_ids = {p["id"] for p in response.data}
        assert foreign_project.pk not in returned_ids


class TestProjectImageViewSet:
    urls = BaseTestModel.get_urls(ProjectImage)
    list_create_url = urls[1]

    def detail_url(self, pk):
        return self.urls[0](pk)

    @staticmethod
    def _create_project_for_branch(branch):
        project = project_initial_data.create_object()
        project.branch = branch
        project.branch.open_time = branch_initial_data.request_data["open_time"]
        project.branch.closed_time = branch_initial_data.request_data["closed_time"]
        project.branch.save()
        project.save()
        return project

    @staticmethod
    def _create_image_for_project(project):
        return ProjectImage.objects.create(
            project=project,
            image=create_image(),
            temporal=FuelTypeChoices.FULL,
        )

    @staticmethod
    def _create_data(project):
        return {
            "project": project.id,
            "image": create_image(),
            "temporal": TemporalChoices.AFTER,
        }

    # ---------------- create ----------------

    def test_create_with_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.post(
            self.list_create_url, data=self._create_data(project), format="multipart"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert ProjectImage.objects.filter(project=project).exists()

    def test_create_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.post(
            self.list_create_url, data=self._create_data(project), format="multipart"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_without_allowed_branch_forbidden(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.post(
            self.list_create_url, data=self._create_data(project), format="multipart"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not ProjectImage.objects.filter(project=project).exists()

    def test_create_super_user_without_allowed_branch_forbidden(self, api_client, super_user):
        """
        Unlike ProjectViewSet.perform_create (which exempts superusers via
        `and not user.is_superuser`), this create() has no such exemption -
        superusers are subject to the same allowed_branches check as
        everyone else.
        """
        project = self._create_project_for_branch(super_user.active_branch)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.post(
            self.list_create_url, data=self._create_data(project), format="multipart"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_unauthenticated(self, client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        response = client.post(
            self.list_create_url, data=self._create_data(project), format="multipart"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_denied_if_project_from_other_smoothing(
            self, api_client, normal_user, owner_user
    ):
        foreign_project = self._create_project_for_branch(owner_user.active_branch)
        normal_user.allowed_branches.add(owner_user.active_branch)
        api_client.force_authenticate(normal_user)

        response = api_client.post(
            self.list_create_url, data=self._create_data(foreign_project), format="multipart"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not ProjectImage.objects.filter(project=foreign_project).exists()

    # ---------------- retrieve ----------------

    def test_retrieve_owner_with_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_owner_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_super_user_without_allowed_branch_not_found(self, api_client, super_user):
        """No superuser bypass anymore - same rule for everyone."""
        project = self._create_project_for_branch(super_user.active_branch)
        image = self._create_image_for_project(project)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        image = self._create_image_for_project(project)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_cross_smoothing_not_found(self, api_client, owner_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        image = self._create_image_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_user_without_active_branch_forbidden(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        image = self._create_image_for_project(project)
        admin_user.active_branch = None
        admin_user.save()

        api_client.force_authenticate(admin_user)
        response = api_client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_unauthenticated(self, client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)

        response = client.get(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---------------- update / delete ----------------

    def test_update_requires_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(image.pk), data={"temporal": TemporalChoices.BEFORE})
        assert response.status_code == status.HTTP_200_OK

    def test_update_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(image.pk), data={"temporal": TemporalChoices.BEFORE})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_requires_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectImage.objects.filter(pk=image.pk).exists()

    def test_delete_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        image = self._create_image_for_project(project)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(image.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert ProjectImage.objects.filter(pk=image.pk).exists()

    # ---------------- list ----------------

    def test_list_returns_only_allowed_branches_images(self, api_client, owner_user, super_user):
        own_project = self._create_project_for_branch(owner_user.active_branch)
        own_image = self._create_image_for_project(own_project)

        other_project = self._create_project_for_branch(super_user.active_branch)
        self._create_image_for_project(other_project)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {i["id"] for i in response.data}
        assert own_image.pk in returned_ids

    def test_list_super_user_without_allowed_branch_sees_nothing(self, api_client, super_user):
        """No superuser bypass anymore for list either."""
        project = self._create_project_for_branch(super_user.active_branch)
        self._create_image_for_project(project)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_unauthenticated(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_user_without_active_branch_forbidden(self, api_client, admin_user):
        admin_user.active_branch = None
        admin_user.save()
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFixItemViewSet:
    """Same permission model as ProjectImageViewSet - see class docstring there."""

    urls = BaseTestModel.get_urls(FixItem)
    list_create_url = urls[1]

    def detail_url(self, pk):
        return self.urls[0](pk)

    @staticmethod
    def _create_project_for_branch(branch):
        project = project_initial_data.create_object()
        project.branch = branch
        project.branch.open_time = branch_initial_data.request_data["open_time"]
        project.branch.closed_time = branch_initial_data.request_data["closed_time"]
        project.branch.save()
        project.save()
        return project

    @staticmethod
    def _create_fix_area():
        main_part = MainPart.objects.create(name="body")
        return FixArea.objects.create(main_part=main_part, name="door")

    @classmethod
    def _create_fix_item_for_project(cls, project):
        return FixItem.objects.create(
            project=project,
            fix_type=FixTypeChoices.SMOOTHING,
            fix_area=cls._create_fix_area(),
            number_of_days=2,
            amount=1000,
        )

    @classmethod
    def _create_data(cls, project):
        return {
            "project": project.id,
            "fix_type": FixTypeChoices.SMOOTHING,
            "fix_area": cls._create_fix_area().id,
            "number_of_days": 2,
            "amount": 1000,
        }

    # ---------------- create ----------------

    def test_create_with_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.list_create_url, data=self._create_data(project))
        assert response.status_code == status.HTTP_201_CREATED
        assert FixItem.objects.filter(project=project).exists()

    def test_create_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.post(self.list_create_url, data=self._create_data(project))
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_without_allowed_branch_forbidden(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.list_create_url, data=self._create_data(project))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not FixItem.objects.filter(project=project).exists()

    def test_create_super_user_without_allowed_branch_forbidden(self, api_client, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.post(self.list_create_url, data=self._create_data(project))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_unauthenticated(self, client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        response = client.post(self.list_create_url, data=self._create_data(project))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_denied_if_project_from_other_smoothing(
            self, api_client, normal_user, owner_user
    ):
        """Same fix as ProjectImageViewSet - see its docstring."""
        foreign_project = self._create_project_for_branch(owner_user.active_branch)
        normal_user.allowed_branches.add(owner_user.active_branch)
        api_client.force_authenticate(normal_user)

        response = api_client.post(self.list_create_url, data=self._create_data(foreign_project))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not FixItem.objects.filter(project=foreign_project).exists()

    # ---------------- retrieve ----------------

    def test_retrieve_owner_with_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_owner_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_super_user_without_allowed_branch_not_found(self, api_client, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_admin_with_allowed_branch(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_cross_smoothing_not_found(self, api_client, owner_user, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_user_without_active_branch_forbidden(self, api_client, admin_user):
        project = self._create_project_for_branch(admin_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        admin_user.active_branch = None
        admin_user.save()

        api_client.force_authenticate(admin_user)
        response = api_client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_unauthenticated(self, client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)

        response = client.get(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---------------- update / delete ----------------

    def test_update_requires_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(fix_item.pk), data={"amount": 2000})
        assert response.status_code == status.HTTP_200_OK
        fix_item.refresh_from_db()
        assert fix_item.amount == 2000

    def test_update_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(fix_item.pk), data={"amount": 2000})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_requires_allowed_branch(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FixItem.objects.filter(pk=fix_item.pk).exists()

    def test_delete_without_allowed_branch_not_found(self, api_client, owner_user):
        project = self._create_project_for_branch(owner_user.active_branch)
        fix_item = self._create_fix_item_for_project(project)
        owner_user.allowed_branches.remove(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(fix_item.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert FixItem.objects.filter(pk=fix_item.pk).exists()

    # ---------------- list ----------------

    def test_list_returns_only_allowed_branches_fix_items(self, api_client, owner_user, super_user):
        own_project = self._create_project_for_branch(owner_user.active_branch)
        own_fix_item = self._create_fix_item_for_project(own_project)

        other_project = self._create_project_for_branch(super_user.active_branch)
        self._create_fix_item_for_project(other_project)

        api_client.force_authenticate(owner_user)
        response = api_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {f["id"] for f in response.data}
        assert own_fix_item.pk in returned_ids

    def test_list_super_user_without_allowed_branch_sees_nothing(self, api_client, super_user):
        project = self._create_project_for_branch(super_user.active_branch)
        self._create_fix_item_for_project(project)
        super_user.allowed_branches.remove(super_user.active_branch)
        api_client.force_authenticate(super_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_unauthenticated(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_user_without_active_branch_forbidden(self, api_client, admin_user):
        admin_user.active_branch = None
        admin_user.save()
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
