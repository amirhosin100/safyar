from unittest.mock import patch, MagicMock

import pytest
from django.urls import reverse
from rest_framework import status

from apps.costumer.tests.fixtures.data import costumer_initial_data

pytestmark = pytest.mark.django_db


class TestSendBulkSMSAPIView:
    url = reverse("smoothing:send-bulk-sms")

    def test_correct(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        with patch("apps.core.sms.sms_class.send_bulk_sms") as mock:
            response = api_client.post(self.url, data={"message": "test_message"})
            assert response.status_code == status.HTTP_200_OK
            assert mock.call_count == 0

    def test_with_costumer(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        costumer = costumer_initial_data.create_object()
        costumer.branch = owner_user.active_branch
        costumer.save()

        with patch("apps.core.sms.sms_class.send_bulk_sms") as mock:
            response = api_client.post(self.url, data={"message": "test_message"})
            assert response.status_code == status.HTTP_200_OK
            assert mock.call_count == 1

    def test_messages_grater_then_100(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        phone_numbers = []
        for i in range(110):
            phone_numbers.append(i)

        with patch("apps.smoothing.views.Costumer.objects.filter.values_list") as values_mock:
            values_mock.return_value = phone_numbers
            with patch("apps.core.sms.sms_class.send_bulk_sms") as mock:
                response = api_client.post(self.url, data={"message": "test_message"})
                assert response.status_code == status.HTTP_200_OK
                assert mock.call_count == 2

