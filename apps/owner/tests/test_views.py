from apps.core.tests.base_test import BaseTestView
from apps.owner.models import Version, UsageMethod


class TestVersionView(BaseTestView):
    model = Version


class TestUsageMethodView(BaseTestView):
    model = UsageMethod
