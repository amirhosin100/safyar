from django.apps import AppConfig


class WalletConfig(AppConfig):
    name = 'apps.wallet'

    def ready(self):
        import apps.wallet.signals
