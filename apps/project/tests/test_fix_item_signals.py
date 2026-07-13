import pytest

from apps.project.choices import FixTypeChoices
from apps.project.models import FixItem, MainPart, FixArea
from apps.project.tests.fixtures.data import project_initial_data
from apps.smoothing.choices import JobTypeChoices
from apps.smoothing.models import Colleague

pytestmark = pytest.mark.django_db


class TestFixItemProjectTotalsSignal:

    @staticmethod
    def _create_project():
        return project_initial_data.create_object()

    @staticmethod
    def _create_fix_area(name="door"):
        main_part = MainPart.objects.create(name="body")
        return FixArea.objects.create(main_part=main_part, name=name)

    @staticmethod
    def _create_colleague(branch, name="repairman"):
        return Colleague.objects.create(
            branch=branch,
            name=name,
            phone_number="09120000000",
            job_type=JobTypeChoices.SMOOTHER,
        )

    def _create_fix_item(self, project, fix_type, amount, discount=0, number_of_days=1, repairman=None):
        return FixItem.objects.create(
            project=project,
            fix_type=fix_type,
            fix_area=self._create_fix_area(),
            amount=amount,
            discount=discount,
            number_of_days=number_of_days,
            repairman=repairman,
        )

    # ---------------- days / price aggregation ----------------

    def test_create_smoothing_fix_item_sets_project_totals(self):
        project = self._create_project()

        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=100, number_of_days=3)

        project.refresh_from_db()
        assert project.smoothing_days == 3
        assert project.smoothing_price == 900
        assert project.mask_days is None
        assert project.mask_price is None
        assert project.paint_days is None
        assert project.paint_price is None

    def test_multiple_fix_items_of_same_type_are_summed(self):
        project = self._create_project()

        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=100, number_of_days=3)
        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=500, discount=0, number_of_days=2)

        project.refresh_from_db()
        assert project.smoothing_days == 5
        assert project.smoothing_price == 1400

    def test_different_types_are_independent(self):
        project = self._create_project()

        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=100, number_of_days=3)
        self._create_fix_item(project, FixTypeChoices.MASK, amount=300, discount=50, number_of_days=1)

        project.refresh_from_db()
        assert project.smoothing_days == 3
        assert project.smoothing_price == 900
        assert project.mask_days == 1
        assert project.mask_price == 250
        assert project.paint_days is None
        assert project.paint_price is None

    def test_changing_fix_type_moves_totals_between_fields(self):
        project = self._create_project()
        fix_item = self._create_fix_item(
            project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=3
        )

        fix_item.fix_type = FixTypeChoices.PAINT
        fix_item.save()

        project.refresh_from_db()
        assert project.smoothing_days is None
        assert project.smoothing_price is None
        assert project.paint_days == 3
        assert project.paint_price == 1000

    # ---------------- delete ----------------

    def test_soft_delete_fix_item_recalculates_totals(self):
        project = self._create_project()
        fix_item_1 = self._create_fix_item(
            project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=3
        )
        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=500, discount=0, number_of_days=2)

        fix_item_1.delete()  # soft delete (BaseModel.delete)

        project.refresh_from_db()
        assert project.smoothing_days == 2
        assert project.smoothing_price == 500

    def test_deleting_all_fix_items_of_a_type_resets_fields_to_none(self):
        project = self._create_project()
        fix_item = self._create_fix_item(project, FixTypeChoices.MASK, amount=300, discount=0, number_of_days=1)

        fix_item.delete()

        project.refresh_from_db()
        assert project.mask_days is None
        assert project.mask_price is None

    def test_hard_delete_via_queryset_also_recalculates(self):
        project = self._create_project()
        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=1)

        FixItem.objects.filter(project=project).delete()

        project.refresh_from_db()
        assert project.smoothing_days is None
        assert project.smoothing_price is None

    # ---------------- colleagues ----------------

    def test_repairman_added_to_project_colleagues(self):
        project = self._create_project()
        colleague = self._create_colleague(project.branch)

        self._create_fix_item(
            project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=1, repairman=colleague
        )

        assert list(project.colleagues.all()) == [colleague]

    def test_multiple_repairmen_are_all_added(self):
        project = self._create_project()
        colleague_1 = self._create_colleague(project.branch, name="repairman 1")
        colleague_2 = self._create_colleague(project.branch, name="repairman 2")

        self._create_fix_item(
            project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=1, repairman=colleague_1
        )
        self._create_fix_item(
            project, FixTypeChoices.MASK, amount=500, discount=0, number_of_days=1, repairman=colleague_2
        )

        colleague_ids = set(project.colleagues.values_list("id", flat=True))
        assert colleague_ids == {colleague_1.id, colleague_2.id}

    def test_fix_item_without_repairman_does_not_add_colleague(self):
        project = self._create_project()

        self._create_fix_item(project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=1)

        assert project.colleagues.count() == 0

    def test_removing_fix_item_removes_colleague_if_no_longer_referenced(self):
        project = self._create_project()
        colleague = self._create_colleague(project.branch)

        fix_item = self._create_fix_item(
            project, FixTypeChoices.SMOOTHING, amount=1000, discount=0, number_of_days=1, repairman=colleague
        )
        fix_item.delete()

        assert project.colleagues.count() == 0