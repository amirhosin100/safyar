from django.apps import AppConfig


class SmoothingConfig(AppConfig):
    name = 'apps.smoothing'


    def ready(self):
        import apps.smoothing.signals