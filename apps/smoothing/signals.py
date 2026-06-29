from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.smoothing.models import Smoothing
from apps.wallet.models import Wallet


@receiver(post_save, sender=Smoothing)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(smoothing=instance,stock=0)

