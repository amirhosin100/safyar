from django.dispatch import receiver
from django.db.models.signals import post_save

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
