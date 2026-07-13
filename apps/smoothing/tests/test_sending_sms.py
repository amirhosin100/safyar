from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.costumer.tests.fixtures.data import costumer_initial_data
from apps.owner.choices import SmsTypeChoices, SmsLogStatusChoices
from apps.owner.models import SmsLog

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

    @staticmethod
    def _create_costumer_for_branch(branch):
        costumer = costumer_initial_data.create_object()
        costumer.branch = branch
        costumer.save()
        return costumer

    # ---------------- success ----------------

    def test_correct_creates_success_log(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_bulk_sms") as mock:
            response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_200_OK
        assert mock.call_count == 0
        # even with no costumers, schedule_bulk_sms returns [] and all([]) is True,
        # so a SUCCESS log is still created
        assert SmsLog.objects.count() == log_count + 1

        log = SmsLog.objects.latest("id")
        assert log.message == "test_message"
        assert log.sms_type == SmsTypeChoices.BULK
        assert log.status == SmsLogStatusChoices.SUCCESS
        assert log.branch == owner_user.active_branch
        assert log.send_by == owner_user

    def test_with_costumer_creates_success_log(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        self._create_costumer_for_branch(owner_user.active_branch)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_bulk_sms") as mock:
            response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_200_OK
        assert mock.call_count == 1
        assert SmsLog.objects.count() == log_count + 1
        assert SmsLog.objects.latest("id").status == SmsLogStatusChoices.SUCCESS

    def test_messages_grater_then_100(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        phone_numbers = list(range(110))
        log_count = SmsLog.objects.count()

        with patch("apps.smoothing.views.Costumer.objects.filter") as filter_mock:
            filter_mock.return_value.values_list.return_value = phone_numbers
            with patch("apps.core.sms.sms_class.send_bulk_sms") as mock:
                response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_200_OK
        assert mock.call_count == 2
        assert SmsLog.objects.count() == log_count + 1
        assert SmsLog.objects.latest("id").status == SmsLogStatusChoices.SUCCESS

    # ---------------- failure ----------------

    def test_failed_send_creates_failed_log_and_returns_400(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        self._create_costumer_for_branch(owner_user.active_branch)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_bulk_sms", return_value=False):
            response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert SmsLog.objects.count() == log_count + 1
        log = SmsLog.objects.latest("id")
        assert log.status == SmsLogStatusChoices.FAILED
        assert log.sms_type == SmsTypeChoices.BULK

    def test_partial_batch_failure_creates_failed_log(self, api_client, owner_user):
        """If even one batch out of many fails, all(result) is False and the whole send is logged as failed."""
        api_client.force_authenticate(owner_user)
        phone_numbers = list(range(110))
        log_count = SmsLog.objects.count()

        with patch("apps.smoothing.views.Costumer.objects.filter") as filter_mock:
            filter_mock.return_value.values_list.return_value = phone_numbers
            with patch("apps.core.sms.sms_class.send_bulk_sms", side_effect=[True, False]):
                response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert SmsLog.objects.count() == log_count + 1
        assert SmsLog.objects.latest("id").status == SmsLogStatusChoices.FAILED

    # ---------------- validation ----------------

    def test_missing_message_returns_400(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)
        log_count = SmsLog.objects.count()

        response = api_client.post(self.url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert SmsLog.objects.count() == log_count

    # ---------------- permissions ----------------

    def test_with_super_user(self, api_client, super_user):
        api_client.force_authenticate(super_user)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_bulk_sms"):
            response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_200_OK
        assert SmsLog.objects.count() == log_count + 1

    def test_with_admin_user_forbidden(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        log_count = SmsLog.objects.count()

        response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert SmsLog.objects.count() == log_count

    def test_with_normal_user_forbidden(self, api_client, normal_user):
        api_client.force_authenticate(normal_user)
        response = api_client.post(self.url, data={"message": "test_message"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client):
        response = client.post(self.url, data={"message": "test_message"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSendSingleSMSAPIView:

    @staticmethod
    def url(costumer_id):
        return reverse("smoothing:send-single-sms", args=[costumer_id])

    @staticmethod
    def _create_costumer_for_branch(branch):
        costumer = costumer_initial_data.create_object()
        costumer.branch = branch
        costumer.branch.smoothing.wallet.stock = 200000
        costumer.branch.smoothing.wallet.save()
        costumer.save()
        return costumer

    # ---------------- success ----------------

    def test_correct_creates_success_log(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_single_sms", return_value=True) as mock:
            response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_200_OK
        assert mock.call_count == 1
        assert mock.call_args[0][0] == costumer.phone_number
        assert SmsLog.objects.count() == log_count + 1

        log = SmsLog.objects.latest("id")
        assert log.message == "hi"
        assert log.sms_type == SmsTypeChoices.SINGLE
        assert log.status == SmsLogStatusChoices.SUCCESS
        assert log.branch == owner_user.active_branch
        assert log.send_by == owner_user

    def test_admin_with_allowed_branch(self, api_client, admin_user):
        costumer = self._create_costumer_for_branch(admin_user.active_branch)
        admin_user.allowed_branches.add(admin_user.active_branch)
        api_client.force_authenticate(admin_user)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_single_sms", return_value=True):
            response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_200_OK
        assert SmsLog.objects.count() == log_count + 1

    # ---------------- failure ----------------

    def test_send_failure_returns_400_and_does_not_log(self, api_client, owner_user):
        """No SmsLog entry is created when the SMS gateway itself fails - only successful sends are logged here."""
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_single_sms", return_value=False):
            response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert SmsLog.objects.count() == log_count

    # ---------------- permissions ----------------

    def test_costumer_not_in_allowed_branches_forbidden(self, api_client, owner_user, super_user):
        costumer = self._create_costumer_for_branch(super_user.active_branch)
        api_client.force_authenticate(owner_user)
        log_count = SmsLog.objects.count()

        with patch("apps.core.sms.sms_class.send_single_sms") as mock:
            response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert mock.call_count == 0
        assert SmsLog.objects.count() == log_count

    def test_admin_without_allowed_branch_forbidden(self, api_client, admin_user):
        costumer = self._create_costumer_for_branch(admin_user.active_branch)
        api_client.force_authenticate(admin_user)
        # admin_user.allowed_branches is intentionally left empty

        response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_normal_user_forbidden(self, api_client, normal_user, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        normal_user.active_branch = owner_user.active_branch
        normal_user.allowed_branches.set([owner_user.active_branch])
        normal_user.save()
        api_client.force_authenticate(normal_user)

        response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_without_active_branch_forbidden(self, api_client, admin_user):
        costumer = self._create_costumer_for_branch(admin_user.active_branch)
        admin_user.active_branch = None
        admin_user.save()
        api_client.force_authenticate(admin_user)

        response = api_client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated(self, client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)

        response = client.post(self.url(costumer.id), data={"message": "hi"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---------------- validation / not found ----------------

    def test_missing_message_returns_400(self, api_client, owner_user):
        costumer = self._create_costumer_for_branch(owner_user.active_branch)
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.url(costumer.id), data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_costumer_not_found(self, api_client, owner_user):
        api_client.force_authenticate(owner_user)

        response = api_client.post(self.url(999999), data={"message": "hi"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "costumer does not exist"
