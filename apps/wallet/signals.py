from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.wallet.models import Wallet


@receiver(pre_save, sender=Wallet)
def change_wallet_stock_smoothing(sender, instance, **kwargs):
    instance.smoothing.wallet_stock = instance.stock
    instance.save()
