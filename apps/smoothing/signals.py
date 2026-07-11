from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from apps.account.models import User
from apps.core.sms import sms_center
from apps.smoothing.models import Smoothing, Branch
from apps.wallet.models import Wallet


@receiver(post_save, sender=Smoothing)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(smoothing=instance, stock=0)


@receiver(post_save, sender=Wallet)
def update_smoothing_stock(sender, instance, created, **kwargs):
    instance.smoothing.wallet_stock = instance.stock
    instance.smoothing.save()


@receiver(post_save, sender=Branch)
def update_allowed_branches_of_user(sender, instance, created, **kwargs):
    if hasattr(instance.smoothing, "owner_user"):
        owner_user = instance.smoothing.owner_user
        owner_user.allowed_branches.add(instance)


@receiver(pre_save, sender=Smoothing)
def update_user_is_smoothing_active(sender, instance, **kwargs):
    if not instance.pk and hasattr(instance, "_pre_is_active"):
        return

    if instance.is_active != instance._pre_is_active:
        users = User.objects.filter(active_branch__smoothing=instance)
        users.update(is_active_smoothing=instance.is_active)

        if hasattr(instance, "owner_user"):
            if instance.is_active:
                sms_center.send_smoothing_activated_sms(instance.owner_user)
            else:
                sms_center.send_smoothing_deactivated_sms(instance.owner_user)
