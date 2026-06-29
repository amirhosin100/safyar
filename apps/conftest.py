import os
import shutil

import pytest

from apps.account.choices import UserTypeChoices
from apps.account.models import User
from django.conf import settings
from django.test.utils import override_settings
from rest_framework.test import APIClient

from apps.smoothing.models import Smoothing
from apps.smoothing.tests.fixtures.data import smoothing_initial_data


@pytest.fixture
def super_user():
    return User.objects.create_superuser(
        national_code="1234567890",
        phone_number="09123456789",
        full_name="admin"
    )

@pytest.fixture
def owner_user():
    return User.objects.create_user(
        national_code="0987654321",
        phone_number="09876543210",
        full_name="normal_user",
        user_type=UserTypeChoices.OWNER
    )

@pytest.fixture
def normal_user():
    return User.objects.create_user(
        national_code="1234562890",
        phone_number="09176543210",
        full_name="normal_user",
    )


@pytest.fixture
def client():
    api_client_obj = APIClient()
    api_client_obj.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
    return api_client_obj


@pytest.fixture
def api_client(client, super_user):
    client.force_authenticate(super_user)
    return client


@pytest.fixture(autouse=True, scope="session")
def override_media_root():
    with override_settings(
        MEDIA_ROOT=settings.TEST_MEDIA_ROOT,
    ):
        yield
    if os.path.exists(settings.TEST_MEDIA_ROOT):
        shutil.rmtree(settings.TEST_MEDIA_ROOT)

