import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.choices import UserTypeChoices
from apps.account.models import User
from apps.core.tests.base_test import BaseTestView
from apps.smoothing.choices import OrderChoices
from apps.smoothing.models import Smoothing, Branch
from apps.smoothing.tests.fixtures.data import smoothing_initial_data, branch_initial_data

pytestmark = pytest.mark.django_db


class TestSmoothingView(BaseTestView):
    model = Smoothing

    def test_with_normal_user(self, owner_user, api_client):
        api_client.force_authenticate(owner_user)
        self.create_data.set_up()
        response = api_client.post(
            self.list_create_url, data=self.create_data.request_data, format="multipart"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBranchView:
    create_url = BaseTestView.get_urls(Branch)[1]
    urls = BaseTestView.get_urls(Branch)

    @staticmethod
    def create_smoothing(user):
        smoothing = smoothing_initial_data.create_object()
        user.smoothing = smoothing
        user.save()
        return smoothing

    @property
    def branch_data(self):
        data = branch_initial_data.request_data.copy()
        return data

    @staticmethod
    def _create_branch(smoothing, name="extra branch"):
        return Branch.objects.create(smoothing=smoothing, name=name, order=OrderChoices.OTHER)

    @staticmethod
    def _create_owner(national_code, phone_number, full_name="another owner"):
        # OWNER (and SUPER_USER) get their own Smoothing + Branch auto-created in User.save()
        return User.objects.create_user(
            national_code=national_code,
            phone_number=phone_number,
            full_name=full_name,
            user_type=UserTypeChoices.OWNER,
        )

    def detail_url(self, pk):
        return self.urls[0](pk)

    # ---------------- create ----------------

    def test_correct_create(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.post(self.create_url, data=self.branch_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["smoothing"] == owner_user.active_branch.smoothing.pk

    def test_create_with_admin_user(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        response = api_client.post(self.create_url, data=self.branch_data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_superuser_is_scoped_to_own_smoothing(self, api_client, super_user):
        """
        There's no special-casing for superuser anymore in perform_create(), so a
        superuser creates branches under their own smoothing too, same as anyone
        else. (Presumably this is what the planned dedicated superuser view will
        change.)
        """
        api_client.force_authenticate(super_user)
        response = api_client.post(self.create_url, data=self.branch_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["smoothing"] == super_user.active_branch.smoothing.pk

    def test_create_ignores_client_submitted_smoothing(self, api_client, owner_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        data = self.branch_data
        data["smoothing"] = other_owner.active_branch.smoothing.pk

        api_client.force_authenticate(owner_user)
        response = api_client.post(self.create_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        # `smoothing` is read-only - the submitted value is ignored, own smoothing is used
        assert response.data["smoothing"] == owner_user.active_branch.smoothing.pk

    def test_with_normal_user(self, api_client, normal_user, owner_user):
        api_client.force_authenticate(normal_user)
        normal_user.active_branch = owner_user.active_branch
        normal_user.save()

        response = api_client.post(self.create_url, data=self.branch_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_unauthenticated(self, client):
        response = client.post(self.create_url, data=self.branch_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---------------- retrieve ----------------

    def test_retrieve_owner_own_branch(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.detail_url(owner_user.active_branch.pk))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == owner_user.active_branch.pk

    def test_retrieve_owner_other_branch_same_smoothing(self, api_client, owner_user):
        # OWNER's object permission only checks smoothing match, not allowed_branches,
        # so an owner can access any branch within their own smoothing.
        other_branch = self._create_branch(owner_user.active_branch.smoothing, name="another branch")
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(other_branch.pk))

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_cross_smoothing_returns_404(self, api_client, owner_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.detail_url(other_owner.active_branch.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_admin_with_allowed_branch(self, api_client, admin_user):
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(admin_user.active_branch.pk))

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_admin_without_allowed_branch_forbidden(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.detail_url(admin_user.active_branch.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_superuser_without_allowed_branches_forbidden(self, api_client, super_user):
        api_client.force_authenticate(super_user)
        response = api_client.get(self.detail_url(super_user.active_branch.pk))

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_normal_user_forbidden(self, api_client, normal_user, owner_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.detail_url(owner_user.active_branch.pk))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_unauthenticated(self, client, owner_user):
        response = client.get(self.detail_url(owner_user.active_branch.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---------------- list ----------------

    def test_list_filters_by_smoothing(self, api_client, owner_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        api_client.force_authenticate(owner_user)

        response = api_client.get(self.create_url)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {branch["id"] for branch in response.data}
        assert owner_user.active_branch.pk in returned_ids
        assert other_owner.active_branch.pk not in returned_ids

    def test_list_superuser_scoped_to_own_smoothing(self, api_client, super_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        api_client.force_authenticate(super_user)

        response = api_client.get(self.create_url)

        assert response.status_code == status.HTTP_200_OK
        returned_ids = {branch["id"] for branch in response.data}
        assert super_user.active_branch.pk in returned_ids
        assert other_owner.active_branch.pk not in returned_ids

    def test_list_admin_ignores_allowed_branches(self, api_client, admin_user):
        """
        NOTE: get_queryset() still only filters by `smoothing`, not `allowed_branches`.
        So list can return a branch that a subsequent retrieve on the same id would
        403 on (see test_retrieve_admin_without_allowed_branch_forbidden). List and
        detail are inconsistent here.
        """
        self._create_branch(admin_user.active_branch.smoothing, name="not allowed")
        api_client.force_authenticate(admin_user)

        response = api_client.get(self.create_url)

        assert response.status_code == status.HTTP_200_OK

    # ---------------- update ----------------

    def test_update_owner(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.patch(self.detail_url(owner_user.active_branch.pk), data={"name": "updated name"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "updated name"

    def test_update_smoothing_field_is_ignored(self, api_client, owner_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        api_client.force_authenticate(owner_user)

        response = api_client.patch(
            self.detail_url(owner_user.active_branch.pk),
            data={"name": "still mine", "smoothing": other_owner.active_branch.smoothing.pk},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "still mine"
        assert response.data["smoothing"] == owner_user.active_branch.smoothing.pk

    def test_update_cross_smoothing_returns_404(self, api_client, owner_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        api_client.force_authenticate(owner_user)

        response = api_client.patch(self.detail_url(other_owner.active_branch.pk), data={"name": "hacked"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_admin_with_allowed_branch(self, api_client, admin_user):
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.patch(self.detail_url(admin_user.active_branch.pk), data={"name": "updated by admin"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "updated by admin"

    def test_update_admin_without_allowed_branch_forbidden(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        response = api_client.patch(self.detail_url(admin_user.active_branch.pk), data={"name": "hacked"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_normal_user_forbidden(self, api_client, normal_user, owner_user):
        api_client.force_authenticate(normal_user)
        response = api_client.patch(self.detail_url(owner_user.active_branch.pk), data={"name": "hacked"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ---------------- delete ----------------

    def test_delete_owner(self, api_client, owner_user):
        extra_branch = self._create_branch(owner_user.active_branch.smoothing)
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(extra_branch.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Branch.objects.filter(pk=extra_branch.pk).exists()

    def test_delete_cross_smoothing_returns_404(self, api_client, owner_user, create_user):
        other_owner = create_user(national_code="1010101010", phone_number="09101010101")
        api_client.force_authenticate(owner_user)

        response = api_client.delete(self.detail_url(other_owner.active_branch.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Branch.objects.filter(pk=other_owner.active_branch.pk).exists()

    def test_delete_admin_with_allowed_branch(self, api_client, admin_user):
        extra_branch = self._create_branch(admin_user.active_branch.smoothing)
        admin_user.active_branch = extra_branch
        admin_user.allowed_branches.add(extra_branch)
        api_client.force_authenticate(admin_user)

        response = api_client.delete(self.detail_url(extra_branch.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Branch.objects.filter(pk=extra_branch.pk).exists()

    def test_delete_admin_without_allowed_branch_not_found(self, api_client, admin_user):
        extra_branch = self._create_branch(admin_user.active_branch.smoothing)
        api_client.force_authenticate(admin_user)

        response = api_client.delete(self.detail_url(extra_branch.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Branch.objects.filter(pk=extra_branch.pk).exists()

    def test_delete_normal_user_forbidden(self, api_client, normal_user, owner_user):
        api_client.force_authenticate(normal_user)
        response = api_client.delete(self.detail_url(owner_user.active_branch.pk))

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSmoothingAPIView:
    url = reverse("smoothing:user-smoothing")

    # get
    def test_get_owner(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == owner_user.active_branch.smoothing.pk

    def test_get_admin(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # put / patch
    def test_put_crashes_due_to_missing_return(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        api_client.put(self.url, data={"address": "new address"})

    def test_patch_crashes_due_to_missing_return(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        api_client.patch(self.url, data={"address": "new address"})

        assert owner_user.smoothing.address == "new address"


class TestBranchAPIView:
    url = reverse("smoothing:branch-smoothing")

    # get
    def test_get_owner(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == owner_user.active_branch.pk

    def test_get_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_admin_without_branch_does_not_crash(self, client):
        admin_without_branch = User.objects.create_user(
            national_code="7777777777",
            phone_number="09777777777",
            full_name="branchless admin",
            user_type=UserTypeChoices.ADMIN,
        )
        client.force_authenticate(admin_without_branch)

        response = client.get(self.url)

        assert response.status_code == status.HTTP_200_OK

    # put / patch
    def test_put_crashes_due_to_missing_return(self, api_client, owner_user):
        """Same missing-`return` bug as SmoothingAPIView.put(), see there for details."""
        api_client.force_authenticate(owner_user)

        api_client.put(self.url, data={"name": "updated branch", "order": 1})

    def test_patch_crashes_due_to_missing_return(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)

        api_client.patch(self.url, data={"name": "updated branch"})
