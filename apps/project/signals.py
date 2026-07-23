from django_redis import get_redis_connection

from apps.core.sms import sms_center
from apps.core.utils.prefix import access_codes
from apps.project.choices import FixTypeChoices, ProjectStatusChoices
from apps.project.models import FixItem, Project
from django.db.models import F, Sum, Max
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.smoothing.models import Branch

redis = get_redis_connection()


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

    #TODO write test for it
    if Project.status == ProjectStatusChoices.DELIVERED:
        keys = redis.smembers(access_codes.format(model_name=Project.__name__,object_id=instance.pk))
        if keys:
            redis.delete(*keys)

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
    amount = 0
    project = Project.objects.get(pk=project_id)

    for days, price in FIX_TYPE_FIELDS.values():
        setattr(project, days, None)
        setattr(project, price, None)

    for row in aggregates:
        fields = FIX_TYPE_FIELDS.get(row["fix_type"])
        if fields is None:
            continue
        days_field, price_field = fields
        setattr(project, days_field, row["total_days"])
        setattr(project, price_field, row["total_price"])
        amount += row["total_price"]

    project.amount = amount
    project.save()

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
        max_code = Project.objects.filter(branch=branch).aggregate(Max("code"))["code__max"]

        if max_code is not None:
            instance.code = max_code + 1
        else:
            instance.code = branch.next_follow_up_code

        branch.next_follow_up_code = instance.code + 1
        branch.save()
