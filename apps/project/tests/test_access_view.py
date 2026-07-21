from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from apps.core.access_views import generate_identify
from apps.project.tests.fixtures.data import project_initial_data


pytestmark = pytest.mark.django_db


class TestAccessProjectView:
    url = reverse("project:access")

    @staticmethod
    def get_data(project):
        code = generate_identify(project.id, timezone.now() + timedelta(hours=1))
        return {"identify_code": code}

    def test_correct(self, client):
        project = project_initial_data.create_object()
        data = self.get_data(project)

        response = client.post(self.url, data=data)
        assert response.status_code == 200
        assert response.data["id"] == project.id

    #TODO write more tests

