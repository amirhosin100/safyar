from apps.core.tests.base_test import BaseTestView
from apps.owner.models import Version, UsageMethod


class TestVersionView(BaseTestView):
    model = Version

    def test_with_normal_user(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.list_create_url)
        assert response.status_code == 403

    def test_with_anonymous_user(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == 401


class TestUsageMethodView(BaseTestView):
    model = UsageMethod

    def test_with_normal_user(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.get(self.list_create_url)
        assert response.status_code == 403

    def test_with_anonymous_user(self, client):
        response = client.get(self.list_create_url)
        assert response.status_code == 401
