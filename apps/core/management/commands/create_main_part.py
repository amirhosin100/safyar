from django.core.management.base import BaseCommand

from apps.core.utils.main_part import load_main_parts


class Command(BaseCommand):
    help = "Load MainPart and FixArea records from static/data/main-part.json"

    def handle(self, *args, **options):
        summary = load_main_parts()
        self.stdout.write(
            self.style.SUCCESS(
                "Loaded main parts data: %(main_parts_created)s MainPart(s) and "
                "%(fix_areas_created)s FixArea(s) created."
                % summary
            )
        )