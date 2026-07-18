from apps.core.sms import sms_center
from apps.project.choices import FixTypeChoices, ProjectStatusChoices
from apps.project.models import FixItem, Project
from django.db.models import F, Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.smoothing.models import Branch


@receiver(post_save, sender=Project)
def send_sms(sender, instance, created, **kwargs):
    if created:
        project_status = instance.status
        match project_status:
            case ProjectStatusChoices.CANCELED:
                sms_center.send_canceled_project_sms(instance)
            case ProjectStatusChoices.TURNED:
                sms_center.send_turned_project_sms(instance)
            case ProjectStatusChoices.SUBMITTED:
                sms_center.send_accepted_project_sms(instance)


FIX_TYPE_FIELDS = {
    FixTypeChoices.SMOOTHING: ("smoothing_days", "smoothing_price"),
    FixTypeChoices.MASK: ("mask_days", "mask_price"),
    FixTypeChoices.PAINT: ("paint_days", "paint_price"),
}


def recalculate_project_fix_items(project_id):
    if project_id is None:
        return

    aggregates = (
        FixItem.objects.filter(project_id=project_id)
        .values("fix_type")
        .annotate(
            total_days=Sum("number_of_days"),
            total_price=Sum(F("amount") - F("discount")),
        )
    )

    update_fields = {}
    for days_field, price_field in FIX_TYPE_FIELDS.values():
        update_fields[days_field] = None
        update_fields[price_field] = None

    for row in aggregates:
        fields = FIX_TYPE_FIELDS.get(row["fix_type"])
        if fields is None:
            continue
        days_field, price_field = fields
        update_fields[days_field] = row["total_days"]
        update_fields[price_field] = row["total_price"]

    Project.objects.filter(pk=project_id).update(**update_fields)

    colleague_ids = list(
        FixItem.objects.filter(project_id=project_id, repairman__isnull=False)
        .values_list("repairman_id", flat=True)
        .distinct()
    )
    Project(pk=project_id).colleagues.set(colleague_ids)


@receiver(post_save, sender=FixItem)
def update_project_totals_on_fix_item_save(sender, instance, **kwargs):
    recalculate_project_fix_items(instance.project_id)


@receiver(post_delete, sender=FixItem)
def update_project_totals_on_fix_item_delete(sender, instance, **kwargs):
    recalculate_project_fix_items(instance.project_id)


@receiver(pre_save, sender=Project)
def set_code(sender, instance, **kwargs):
    if instance._state.adding:
        branch = Branch.objects.get(id=instance.branch_id)

        instance.code = branch.next_follow_up_code
        branch.next_follow_up_code += 1
        branch.save()
