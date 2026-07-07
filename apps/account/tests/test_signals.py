import pytest
from apps.account.models import User
from apps.smoothing.models import Branch

pytestmark = pytest.mark.django_db


class TestSignal:
    model = User

    def test_create_branch(self, owner_user):
        smoothing = owner_user.smoothing
        Branch.objects.create(smoothing=smoothing, order=1, name="test_me")

        assert owner_user.allowed_branches.count() == 2
