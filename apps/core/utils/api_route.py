"""
Stable Latin URL segments for CRUD routers.

Translated ``verbose_name_plural`` must NOT control API paths — i18n would
break routes (e.g. ``account/users`` would become a translated segment). Paths are
derived from the model class name instead, matching legacy English-meta routes.
"""

from __future__ import annotations

import re

from django.db import models


def camel_class_name_to_kebab(class_name: str) -> str:
    return re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "-", class_name
    ).lower()


def pluralize_kebab_segments(kebab: str) -> str:
    parts = kebab.split("-")
    if not parts:
        return kebab

    last = parts[-1]

    irregular_last = {
        "user": "users",
        "cargo": "cargos",
        "company": "companies",
    }
    if last in irregular_last:
        parts[-1] = irregular_last[last]
        return "-".join(parts)

    # Already plural or mass nouns common in Django models
    if last in {"settings", "status", "news", "series"}:
        return kebab
    if len(last) > 1 and last.endswith("s") and not last.endswith("ss"):
        return kebab

    if last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
        parts[-1] = last[:-1] + "ies"
    elif last.endswith(("ch", "sh", "x")):
        parts[-1] = last + "es"
    else:
        parts[-1] = last + "s"

    return "-".join(parts)


def get_crud_url_segment(model_cls: type[models.Model]) -> str:
    kebab = camel_class_name_to_kebab(model_cls.__name__)
    return pluralize_kebab_segments(kebab)


def get_crud_api_prefix(model_cls: type[models.Model]) -> str:
    meta = model_cls._meta
    return f"{meta.app_label}/{get_crud_url_segment(model_cls)}"
