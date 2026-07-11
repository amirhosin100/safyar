from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings

from apps.core.sms import sms_center
from apps.wallet.models import Wallet


@receiver(pre_save, sender=Wallet)
def change_wallet_stock_smoothing(sender, instance, **kwargs):
    instance.smoothing.wallet_stock = instance.stock
    instance.save()

    if instance.stock < settings.WALLET_EMPTY_STOCK and instance.is_sent_empty_sms:
        sms_center.send_wallet_stock_empty_sms(instance)
        instance.is_sent_empty_sms = True
        return

    if instance.stock < settings.WALLET_WARNING_STOCK and instance.is_sent_warning_sms:
        sms_center.send_wallet_stock_waring_sms(instance)
        instance.is_sent_warning_sms = True
        return