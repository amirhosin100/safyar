import json
from pathlib import Path

from django.conf import settings

from apps.project.models import MainPart, FixArea

MAIN_PART_DATA_FILE = settings.BASE_DIR / "static" / "data" / "main-part.json"


def load_main_parts(file_path: Path = MAIN_PART_DATA_FILE) -> dict:
    """
    Read main-part.json and create/update MainPart and FixArea records.

    Existing MainPart/FixArea rows are matched by name (get_or_create), so
    running this multiple times is safe and won't create duplicates.

    Returns a summary dict: {"main_parts_created": int, "fix_areas_created": int}
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    main_parts_created = 0
    fix_areas_created = 0

    for part in data:
        main_part, created = MainPart.objects.get_or_create(name=part["name"])
        if created:
            main_parts_created += 1

        for area_name in part["fix_areas"]:
            _, area_created = FixArea.objects.get_or_create(
                main_part=main_part,
                name=area_name,
            )
            if area_created:
                fix_areas_created += 1

    return {
        "main_parts_created": main_parts_created,
        "fix_areas_created": fix_areas_created,
    }