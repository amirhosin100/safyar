from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = 'apps.core'
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from apps.core.auto_generator.auto_generator import pregenerate_all

        pregenerate_all()
