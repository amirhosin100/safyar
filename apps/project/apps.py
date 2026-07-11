from django.apps import AppConfig


class ProjectConfig(AppConfig):
    name = 'apps.project'

    def ready(self):
        import apps.project.signals
