from rest_framework import status

from apps.core.tests.base_test import BaseTestView
from apps.smoothing.models import Smoothing


class TestSmoothingView(BaseTestView):
    model = Smoothing

    def test_with_normal_user(self, normal_user,api_client):
        api_client.force_authenticate(normal_user)
        self.create_data.set_up()
        response = api_client.post(
            self.list_create_url, data=self.create_data.request_data, format="multipart"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
