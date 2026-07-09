from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.account.choices import OwnerRequestChoices
from apps.account.models import OwnerRequest


@receiver(pre_save, sender=OwnerRequest)
def invalid_change_status_from_accepted_to_rejected(sender, instance, **kwargs):
    if instance.pk and hasattr(instance, "_pre_status"):
        if instance.status != instance._pre_status:
            if (
                    instance.status == OwnerRequestChoices.REJECTED and
                    instance._pre_status == OwnerRequestChoices.ACCEPTED
            ):
                raise ValidationError(_("You cannot reject an accepted smoothing"))

