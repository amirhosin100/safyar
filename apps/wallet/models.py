from apps.core.models import BaseModel
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.wallet.choices import TransactionStatusChoices, TransactionTypeChoices


class Wallet(BaseModel):
    smoothing = models.OneToOneField(
        "smoothing.Smoothing",
        on_delete=models.CASCADE,
        verbose_name=_("Smoothing"),
        related_name="wallet",
    )
    stock = models.PositiveBigIntegerField(
        verbose_name=_("Stock"),
        help_text=_("unit is Rial")
    )
    is_sent_warning_sms = models.BooleanField(
        default=False,
        verbose_name=_("Is Sent Warning"),
    )
    is_sent_empty_sms = models.BooleanField(
        default=False,
        verbose_name=_("Is Sent Empty Sms"),
        help_text=_("If this be False and the stock value is empty, project"
                    " will send sms to the wallet's owner")
    )

    class Meta:
        verbose_name = _("Wallet")
        verbose_name_plural = _("Wallets")

    def __str__(self):
        return f"{str(self.smoothing)} - {self.stock}"

    def decrease(self, amount):
        self.stock -= amount
        if self.stock < 0:
            return False
        self.save()
        return True


class WalletTransaction(BaseModel):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        verbose_name=_("Wallet"),
        related_name="transactions",
    )
    amount = models.BigIntegerField(
        verbose_name=_("Amount"),
    )
    status = models.CharField(
        max_length=2,
        choices=TransactionStatusChoices.choices,
        verbose_name=_("Status"),
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionTypeChoices.choices,
        verbose_name=_("Transaction Type"),
    )
    description = models.CharField(
        max_length=255,
        verbose_name=_("Description"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Wallet Transaction")
        verbose_name_plural = _("Wallet Transactions")

    def __str__(self):
        return f"{self.amount} - {self.created_at}"
