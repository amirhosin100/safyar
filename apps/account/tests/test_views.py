# tests/test_login_view.py
import pytest
from django.urls import reverse
from rest_framework import status

from apps.account.choices import UserTypeChoices
from apps.account.models import User, OwnerRequest
from unittest.mock import patch

from apps.smoothing.models import Smoothing, Branch
from apps.smoothing.tests.fixtures.data import branch_initial_data

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("account:login")


@pytest.fixture
def active_user(create_user):
    """An active user with a known password"""
    user = create_user(
        national_code="3748291650",
        phone_number="09121234567",
        full_name="Test User",
        is_active=True,
    )
    user.set_password("StrongPass@123")
    user.save()
    return user


@pytest.fixture
def inactive_user(create_user):
    """An inactive user"""
    user = create_user(
        national_code="6082947315",
        phone_number="09129876543",
        full_name="Inactive User",
        is_active=False,
    )
    user.set_password("StrongPass@123")
    user.save()
    return user


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

    def test_inactive_user_returns_403(self, api_client, inactive_user):
        payload = {
            "national_code": inactive_user.national_code,
            "password": "StrongPass@123",
        }
        response = api_client.post(LOGIN_URL, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data
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


class TestRegisterView:
    url = reverse("account:register")

    @staticmethod
    def _base_data():
        return {
            "full_name": "test name",
            "national_code": "1212880099",
            "phone_number": "09823567890",
            "address": "Yazd",
            "shop_name": "my shop",
            "password1": "StrongPass@123",
            "password2": "StrongPass@123",
        }

    # ── Success ──────────────────────────────────────────────────────────────
    def test_correct(self, api_client):
        response = api_client.post(self.url, self._base_data())

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(national_code="1212880099")
        assert not user.is_active
        assert OwnerRequest.objects.filter(user=user).count() == 1
        assert user.user_type == UserTypeChoices.OWNER

    # ── Duplicate fields ──────────────────────────────────────────────────────
    def test_duplicate_national_code_returns_400(self, api_client, create_user):
        """Registering again with the same national code should return 400."""
        create_user(
            national_code="1212880099",
            phone_number="09100000000",
            full_name="existing user",
            is_active=False,
        )
        response = api_client.post(self.url, self._base_data())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_duplicate_phone_number_returns_400(self, api_client, normal_user, create_user):
        """Registering with a duplicate phone number should return 400."""
        create_user(
            national_code="9999999999",
            phone_number="09823567890",  # same number as base_data
            full_name="existing user",
            is_active=False,
        )
        response = api_client.post(self.url, self._base_data())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    # ── Field validation ──────────────────────────────────────────────────────
    def test_password_mismatch_returns_400(self, api_client):
        data = self._base_data()
        data["password2"] = "DifferentPass@999"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_national_code_returns_400(self, api_client):
        """A national code with an invalid format (e.g. fewer than 10 digits) should return 400."""
        data = self._base_data()
        data["national_code"] = "123"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_phone_number_returns_400(self, api_client):
        """A phone number with an invalid format should return 400."""
        data = self._base_data()
        data["phone_number"] = "0912"
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_fields_returns_400(self, api_client):
        """Sending an empty payload should return 400."""
        response = api_client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_shop_name_returns_400(self, api_client):
        data = self._base_data()
        data.pop("shop_name")
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ── Method not allowed ────────────────────────────────────────────────────
    def test_get_method_not_allowed(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_not_allowed(self, api_client):
        response = api_client.put(self.url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestResetPasswordView:
    verify_code_url = reverse("account:verify-code")
    reset_password_url = reverse("account:reset-password")
    send_sms_url = reverse("account:send-sms")
    login_url = reverse("account:login")

    def test_correct(self, api_client, normal_user):
        data = {
            "national_code": normal_user.national_code,
        }
        api_client.force_authenticate(user=None)
        with patch("apps.account.views.random.choices") as mocker_choices:
            mocker_choices.return_value = "123456"
            response = api_client.post(self.send_sms_url, data)
            assert response.status_code == status.HTTP_200_OK

        data["code"] = "123456"
        response = api_client.post(
            self.verify_code_url,
            data=data
        )
        assert response.status_code == status.HTTP_200_OK
        response = api_client.post(
            self.login_url,
            data={"national_code": normal_user.national_code, "password": "123456"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        data["password1"] = "123456"
        data["password2"] = "123456"

        response = api_client.post(self.reset_password_url, data)
        assert response.status_code == status.HTTP_200_OK

        assert api_client.post(
            self.login_url,
            data={"national_code": normal_user.national_code, "password": "123456"}
        )
        assert response.status_code == status.HTTP_200_OK

    # TODO write more tests


class TestCreateUser:
    url = reverse("account:user-list-create")

    def create_data(self, branch):
        return {
            "full_name": "amir",
            "active_branch": branch.id,
            "national_code": "0987612345",
            "phone_number": "09876512341",
            "user_type": UserTypeChoices.ADMIN,
            "allowed_branches": [branch.id],
            "password": "123456",
        }

    def test_correct(self, api_client, owner_user):
        api_client.force_authenticate(user=owner_user)
        user_count = User.objects.count()
        data = self.create_data(owner_user.active_branch)
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == user_count + 1
        assert User.objects.get(pk=response.data["id"]).allowed_branches.count() == 1

    def test_with_allowed_branches(self, api_client, super_user, owner_user):
        branch = branch_initial_data.create_object()
        branch.smoothing = owner_user.smoothing
        branch.save()
        owner_user.save()

        api_client.force_authenticate(user=owner_user)
        data = self.create_data(owner_user.active_branch)
        data["allowed_branches"].append(branch.id)
        data["active_branch"] = branch.id

        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.get(pk=response.data["id"]).allowed_branches.count() == 2
        assert User.objects.get(pk=response.data["id"]).active_branch == branch

    def test_users(self, api_client, owner_user, super_user):
        for user, count, status_code in ((owner_user, 0, 403), (super_user, 1, 201)):
            api_client.force_authenticate(user=user)
            user_count = User.objects.count()

            data = self.create_data(super_user.active_branch)
            response = api_client.post(self.url, data)

            assert response.status_code == status_code
            assert User.objects.count() == user_count + count

    def test_with_admin_user_who_dont_allowed_branch(self, api_client, owner_user, admin_user):
        api_client.force_authenticate(user=admin_user)
        admin_user.allowed_branches.clear()
        user_count = User.objects.count()

        data = self.create_data(owner_user.active_branch)

        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.count() == user_count

    def test_by_admin_user_who_joined_branch(self, api_client, admin_user, owner_user):
        api_client.force_authenticate(user=admin_user)
        admin_user.allowed_branches.set([owner_user.active_branch])
        user_count = User.objects.count()

        data = self.create_data(owner_user.active_branch)

        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == user_count + 1

    def test_by_invalid_user(self, api_client, super_user, owner_user):
        api_client.force_authenticate(user=owner_user)
        user_count = User.objects.count()

        data = self.create_data(super_user.active_branch)
        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.count() == user_count

    def test_with_anonymous_user(self, api_client, super_user):
        api_client.force_authenticate(user=None)
        user_count = User.objects.count()

        data = self.create_data(super_user.active_branch)
        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert User.objects.count() == user_count


# ── Fixtures ─────────────────────────────────────────────────────────────────
# owner_user, admin_user, super_user, normal_user, api_client are assumed to
# already exist in conftest.py (used elsewhere in this file).

@pytest.fixture
def target_user(owner_user):
    """A normal user in the same branch as owner_user; the subject of update/delete tests."""
    user = User.objects.create(
        national_code="5566778899",
        phone_number="09112223344",
        full_name="Target User",
        user_type=UserTypeChoices.NORMAL,
        active_branch=owner_user.smoothing.branches.first(),
    )
    user.allowed_branches.add(owner_user.smoothing.branches.first())
    return user


@pytest.fixture
def other_branch_user():
    """A normal user belonging to a completely separate smoothing/branch."""
    smoothing = Smoothing.objects.create(
        phone_number="09199999999",
        owner_name="Other Owner",
    )
    branch = Branch.objects.create(smoothing=smoothing, name="Other Branch", order=1)
    user = User.objects.create(
        national_code="1122334455",
        phone_number="09155667788",
        full_name="Other Branch User",
        user_type=UserTypeChoices.NORMAL,
        active_branch=branch,
    )
    user.allowed_branches.add(branch)
    return user


class TestUserUpdateDeleteView:
    """Tests for UserUpdateDeleteView: PUT, PATCH, DELETE."""

    @staticmethod
    def url(user_id):
        return reverse("account:user-delete-update", kwargs={"user_id": user_id})

    @staticmethod
    def _update_data(branch):
        return {
            "full_name": "updated name",
            "active_branch": branch.id,
            "national_code": "6677889900",
            "phone_number": "09223344556",
            "user_type": UserTypeChoices.NORMAL,
            "allowed_branches": [branch.id],
        }

    # ── PUT: success cases ──────────────────────────────────────────────────
    def test_put_by_owner_in_same_branch(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        data = self._update_data(owner_user.active_branch)
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_200_OK
        target_user.refresh_from_db()
        assert target_user.full_name == "updated name"

    def test_put_by_super_user(self, api_client, super_user, target_user):
        api_client.force_authenticate(user=super_user)
        data = self._update_data(target_user.active_branch)
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_200_OK

    def test_put_by_admin_with_allowed_branch(self, api_client, admin_user, target_user):
        admin_user.allowed_branches.set([target_user.active_branch])
        api_client.force_authenticate(user=admin_user)
        data = self._update_data(target_user.active_branch)
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_200_OK

    # ── PUT: permission edge cases ───────────────────────────────────────────
    def test_put_by_admin_without_allowed_branch_returns_403(self, api_client, admin_user, target_user):
        admin_user.allowed_branches.clear()
        api_client.force_authenticate(user=admin_user)
        data = self._update_data(target_user.active_branch)
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_by_owner_on_other_branch_returns_403(self, api_client, owner_user, other_branch_user):
        api_client.force_authenticate(user=owner_user)
        data = self._update_data(other_branch_user.active_branch)
        response = api_client.put(self.url(other_branch_user.id), data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_by_normal_user_returns_403(self, api_client, normal_user, target_user):
        api_client.force_authenticate(user=normal_user)
        data = self._update_data(target_user.active_branch)
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_by_anonymous_returns_401(self, api_client, target_user):
        api_client.force_authenticate(user=None)
        data = self._update_data(target_user.active_branch)
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ── PUT: not found / validation ──────────────────────────────────────────
    def test_put_user_not_found_returns_404(self, api_client, super_user):
        api_client.force_authenticate(user=super_user)
        data = self._update_data(super_user.active_branch)
        response = api_client.put(self.url(999999), data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_missing_required_field_returns_400(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        data = self._update_data(owner_user.active_branch)
        data.pop("full_name")
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_invalid_user_type_returns_400(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        data = self._update_data(owner_user.active_branch)
        data["user_type"] = UserTypeChoices.SUPER_USER
        response = api_client.put(self.url(target_user.id), data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ── PATCH: partial update ────────────────────────────────────────────────
    def test_patch_partial_update_by_owner(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.url(target_user.id), {"full_name": "patched name"})

        assert response.status_code == status.HTTP_200_OK
        target_user.refresh_from_db()
        assert target_user.full_name == "patched name"

    def test_patch_does_not_require_all_fields(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        response = api_client.patch(self.url(target_user.id), {"phone_number": "09300001122"})

        assert response.status_code == status.HTTP_200_OK

    def test_patch_by_normal_user_returns_403(self, api_client, normal_user, target_user):
        api_client.force_authenticate(user=normal_user)
        response = api_client.patch(self.url(target_user.id), {"full_name": "x"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_by_anonymous_returns_401(self, api_client, target_user):
        api_client.force_authenticate(user=None)
        response = api_client.patch(self.url(target_user.id), {"full_name": "x"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_user_not_found_returns_404(self, api_client, super_user):
        api_client.force_authenticate(user=super_user)
        response = api_client.patch(self.url(999999), {"full_name": "x"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ── DELETE: success cases ────────────────────────────────────────────────
    def test_delete_by_owner_in_same_branch(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        user_count = User.objects.count()
        response = api_client.delete(self.url(target_user.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert User.objects.count() == user_count - 1
        assert not User.objects.filter(id=target_user.id).exists()

    def test_delete_by_super_user(self, api_client, super_user, target_user):
        api_client.force_authenticate(user=super_user)
        response = api_client.delete(self.url(target_user.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_by_admin_with_allowed_branch(self, api_client, admin_user, target_user):
        admin_user.allowed_branches.set([target_user.active_branch])
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(self.url(target_user.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT

    # ── DELETE: permission edge cases ────────────────────────────────────────
    def test_delete_by_admin_without_allowed_branch_returns_403(self, api_client, admin_user, target_user):
        admin_user.allowed_branches.clear()
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(self.url(target_user.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_by_owner_on_other_branch_returns_403(self, api_client, owner_user, other_branch_user):
        api_client.force_authenticate(user=owner_user)
        response = api_client.delete(self.url(other_branch_user.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_by_normal_user_returns_403(self, api_client, normal_user, target_user):
        api_client.force_authenticate(user=normal_user)
        response = api_client.delete(self.url(target_user.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_by_anonymous_returns_401(self, api_client, target_user):
        api_client.force_authenticate(user=None)
        response = api_client.delete(self.url(target_user.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ── DELETE: not found ────────────────────────────────────────────────────
    def test_delete_user_not_found_returns_404(self, api_client, super_user):
        api_client.force_authenticate(user=super_user)
        response = api_client.delete(self.url(999999))

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserListView:
    """Tests for the GET (list) endpoint of UserListCreateView."""

    url = reverse("account:user-list-create")

    # ── Success cases ─────────────────────────────────────────────────────────
    def test_list_by_owner_returns_users_in_own_branch(self, api_client, owner_user, target_user):
        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        returned_codes = [u["national_code"] for u in response.data]
        assert target_user.national_code in returned_codes

    def test_list_excludes_users_from_other_branches(self, api_client, owner_user, other_branch_user):
        api_client.force_authenticate(user=owner_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        returned_codes = [u["national_code"] for u in response.data]
        assert other_branch_user.national_code not in returned_codes

    def test_list_by_admin_returns_users_in_own_branch(self, api_client, admin_user, target_user):
        target_user.active_branch = admin_user.active_branch
        target_user.save()
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        returned_codes = [u["national_code"] for u in response.data]
        assert target_user.national_code in returned_codes

    # ── Permission edge cases ────────────────────────────────────────────────
    def test_list_by_normal_user_returns_403(self, api_client, normal_user):
        api_client.force_authenticate(user=normal_user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_by_anonymous_returns_401(self, api_client):
        api_client.force_authenticate(user=None)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ── Method not allowed ────────────────────────────────────────────────────
    def test_delete_method_not_allowed(self, api_client, owner_user):
        api_client.force_authenticate(user=owner_user)
        response = api_client.delete(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
