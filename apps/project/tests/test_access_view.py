import time
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import status

from apps.core.access_views import generate_identify
from apps.core.utils.prefix import access_code
from apps.project.tests.fixtures.data import project_initial_data

pytestmark = pytest.mark.django_db

redis_conn = get_redis_connection()


class TestAccessProjectView:
    url = reverse("project:access")

    @staticmethod
    def get_data(project_id, expire_time=None):
        """Generate a fresh identify code and return (code, request_payload)."""
        expire_time = expire_time or (timezone.now() + timedelta(hours=1))
        code = generate_identify(project_id, expire_time)
        return code, {"identify_code": code}

    # ---------------- happy path ----------------

    def test_correct(self, client):
        project = project_initial_data.create_object()
        code, data = self.get_data(project.id)

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == project.id

    def test_response_contains_serialized_project_data(self, client):
        """Sanity check that the actual project data is returned, not just the id."""
        project = project_initial_data.create_object()
        _, data = self.get_data(project.id)

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["kilometer_of_car"] == project.kilometer_of_car
        assert response.data["car"] == project.car_id

    def test_code_works_without_any_authentication(self, client):
        project = project_initial_data.create_object()
        _, data = self.get_data(project.id)

        response = client.post(self.url, data=data)
        assert response.status_code == status.HTTP_200_OK

    def test_code_works_for_any_authenticated_user_regardless_of_smoothing(
            self, api_client, owner_user, super_user
    ):
        """
        AccessView has no ownership / branch / smoothing check at all - the
        code itself is the only "permission" checked. So an authenticated
        user from a completely different smoothing can still view another
        smoothing's project as long as they have a valid code for it.
        """
        project = project_initial_data.create_object()
        project.branch = super_user.active_branch
        project.save()
        _, data = self.get_data(project.id)

        api_client.force_authenticate(owner_user)
        response = api_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == project.id

    def test_code_can_be_used_multiple_times(self, client):
        project = project_initial_data.create_object()
        _, data = self.get_data(project.id)

        for _ in range(3):
            response = client.post(self.url, data=data)
            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == project.id

    def test_two_different_codes_for_two_different_projects_are_independent(self, client):
        project_1 = project_initial_data.create_object()
        project_2 = project_initial_data.create_object()
        _, data_1 = self.get_data(project_1.id)
        _, data_2 = self.get_data(project_2.id)

        response_1 = client.post(self.url, data=data_1)
        response_2 = client.post(self.url, data=data_2)

        assert response_1.status_code == status.HTTP_200_OK
        assert response_2.status_code == status.HTTP_200_OK
        assert response_1.data["id"] == project_1.id
        assert response_2.data["id"] == project_2.id

    # ---------------- missing / invalid code ----------------

    def test_missing_identify_code_returns_400(self, client):
        response = client.post(self.url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "identify_code is required"

    def test_null_identify_code_returns_400(self, client):
        # sent as real JSON so `None` actually arrives as Python None,
        # not the multipart-encoded string "None"
        response = client.post(self.url, data={"identify_code": None}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "identify_code is required"

    def test_random_identify_code_returns_400(self, client):
        response = client.post(self.url, data={"identify_code": "not-a-real-code"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "this code is invalid or expired"

    def test_empty_identify_code_returns_400(self, client):
        """An empty string is not None, so it skips the "required" check and
        falls through to the redis lookup, which simply misses."""
        response = client.post(self.url, data={"identify_code": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "this code is invalid or expired"

    def test_whitespace_identify_code_returns_400(self, client):
        response = client.post(self.url, data={"identify_code": "   "})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "this code is invalid or expired"

    # ---------------- expiration ----------------

    def test_expired_code_returns_400(self, client):
        project = project_initial_data.create_object()
        code, data = self.get_data(project.id)

        # simulate time passing by directly removing the redis key,
        # instead of sleeping in the test
        redis_conn.delete(access_code.format(identify=code))

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "this code is invalid or expired"

    def test_code_really_expires_after_its_ttl(self, client):
        """Slower end-to-end test confirming the TTL passed to redis's SET is
        actually honored, not just simulated by deleting the key."""
        project = project_initial_data.create_object()
        _, data = self.get_data(project.id, expire_time=timezone.now() + timedelta(seconds=2))

        time.sleep(2.2)

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "this code is invalid or expired"

    def test_code_still_valid_right_before_expiry(self, client):
        project = project_initial_data.create_object()
        _, data = self.get_data(project.id, expire_time=timezone.now() + timedelta(seconds=5))

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_200_OK

    def test_generate_identify_with_past_expire_time_does_not_crash(self):
        project = project_initial_data.create_object()
        past_time = timezone.now() - timedelta(hours=1)

        with pytest.raises(ValueError):
            generate_identify(project.id, past_time)


    # ---------------- underlying object missing ----------------

    def test_soft_deleted_project_returns_404(self, client):
        project = project_initial_data.create_object()
        code, data = self.get_data(project.id)

        project.delete()  # BaseModel.delete() -> soft delete (deleted=True)

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Project not found"

    def test_code_for_nonexistent_project_id_returns_404(self, client):
        _, data = self.get_data(project_id=999999)

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Project not found"

    # ---------------- HTTP method ----------------

    def test_get_method_not_allowed(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_not_allowed(self, client):
        response = client.put(self.url, data={})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_not_allowed(self, client):
        response = client.delete(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED