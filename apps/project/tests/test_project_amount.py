import pytest
from rest_framework.exceptions import ValidationError

from apps.project.choices import FixTypeChoices
from apps.project.models import FixItem, MainPart, FixArea
from apps.project.tests.fixtures.data import project_initial_data

pytestmark = pytest.mark.django_db


class TestProjectAmountFromFixItems:

    @staticmethod
    def _create_project():
        return project_initial_data.create_object()

    @staticmethod
    def _create_fix_area(name="door"):
        main_part = MainPart.objects.create(name="body")
        return FixArea.objects.create(main_part=main_part, name=name)

    def _create_fix_item(self, project, fix_type, amount, discount=0, number_of_days=1):
        return FixItem.objects.create(
            project=project,
            fix_type=fix_type,
            fix_area=self._create_fix_area(),
            amount=amount,
            discount=discount,
            number_of_days=number_of_days,
        )

    # ---------------- amount = sum of fix_items ----------------

    def test_default_amounts_on_creation_are_zero(self):
        project = self._create_project()
        assert project.amount == 100
        assert project.amount_paid == 0
        assert project.remaining_amount == 100

    def test_amount_equals_sum_of_all_fix_items_across_types(self):
        project = self._create_project()

        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=100, number_of_days=3)
        self._create_fix_item(project, FixTypeChoices.MASK, amount=500, discount=50, number_of_days=1)
        self._create_fix_item(project, FixTypeChoices.PAINT, amount=2000, discount=200, number_of_days=2)

        project.refresh_from_db()
        expected = (1000 - 100) + (500 - 50) + (2000 - 200)
        assert project.amount == expected

    def test_amount_updates_after_deleting_a_fix_item(self):
        project = self._create_project()
        fix_item_1 = self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0)
        self._create_fix_item(project, FixTypeChoices.MASK, amount=500, discount=0)

        fix_item_1.delete()  # soft delete

        project.refresh_from_db()
        assert project.amount == 500

    # ---------------- amount_paid validation ----------------

    def test_amount_paid_equal_to_amount_is_allowed(self):
        project = self._create_project()
        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0)
        project.refresh_from_db()

        project.amount_paid = project.amount
        project.save()  # should not raise

        project.refresh_from_db()
        assert project.remaining_amount == 0

    def test_amount_paid_less_than_amount_sets_correct_remaining_amount(self):
        project = self._create_project()
        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0)
        project.refresh_from_db()

        project.amount_paid = 300
        project.save()

        project.refresh_from_db()
        assert project.remaining_amount == project.amount - 300

    def test_amount_paid_greater_than_amount_raises_validation_error(self):
        project = self._create_project()
        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0)
        project.refresh_from_db()

        project.amount_paid = project.amount + 1
        with pytest.raises(ValidationError):
            project.save()

    # ---------------- documents current (possibly unwanted) behavior ----------------

    def test_remaining_amount_not_auto_synced_when_fix_item_is_added_later(self):
        project = self._create_project()
        project.amount_paid = 0
        project.save()
        assert project.remaining_amount == 100

        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0)

        project.refresh_from_db()
        assert project.amount == 1000
        assert project.remaining_amount == 1000
        assert project.paint_price == 0