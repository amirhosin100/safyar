import importlib
from typing import Dict, Type

from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet
from apps.core.base_classes.base_serializer import BaseModelSerializer, BaseSimpleSerializer
from apps.core.base_classes.base_viewset import BaseProtectionViewSet
from apps.core.base_classes.import_export_only_viewset import ImportExportOnlyViewSet

FULL_SERIALIZERS: Dict[str, Type[serializers.ModelSerializer]] = {}
SIMPLE_SERIALIZERS: Dict[str, Type[serializers.ModelSerializer]] = {}
EXPORT_SERIALIZERS: Dict[str, Type[serializers.ModelSerializer]] = {}
VIEWSETS: Dict[str, Type[ModelViewSet]] = {}
IMPORT_EXPORT_VIEWSETS: Dict[str, Type[ModelViewSet]] = {}


def model_key(model: Type[Model]) -> str:
    return model._meta.label_lower


def get_or_create_serializer(
    model: Type[Model], report_type: str
) -> Type[serializers.ModelSerializer]:
    """
    Get or create serializer based on report_type
    report_type: 'full', 'simple', or 'export'
    """
    key = model_key(model)

    # Select the appropriate cache and base class
    if report_type == "full":
        cache = FULL_SERIALIZERS
        base_class = BaseModelSerializer
        serializer_suffix = "Serializer"
    elif report_type == "simple":
        cache = SIMPLE_SERIALIZERS
        base_class = BaseSimpleSerializer
        serializer_suffix = "SimpleSerializer"
    else:
        raise ValueError(
            _("Invalid report_type. Must be 'full', 'simple'")
        )

    # Create serializer if not exists
    if key not in cache:
        name = model._meta.object_name
        write_only_fields = []
        if hasattr(model, "get_write_only_fields"):
            write_only_fields = model.get_write_only_fields()

        meta_exclude: tuple[str, ...]
        try:
            model._meta.get_field("deleted")
        except FieldDoesNotExist:
            meta_exclude = tuple()
        else:
            meta_exclude = ("deleted",)

        Meta = type(
            "Meta",
            (),
            {
                "model": model,
                "exclude": meta_exclude,
                "extra_kwargs": {
                    key: {"write_only": True} for key in write_only_fields
                },
            },
        )

        cache[key] = type(
            f"{name}{serializer_suffix}",
            (base_class,),
            {"Meta": Meta},
        )

    return cache[key]


def save_viewsets_from_file(model: Type[Model]) -> bool:
    key = model_key(model)
    name = model._meta.object_name
    app_label = model._meta.app_label
    viewset_name = f"{name}ViewSet"

    try:
        app_views = importlib.import_module(f"apps.{app_label}.views")
    except ImportError:
        return False

    if not hasattr(app_views, viewset_name):
        return False

    VIEWSETS[key] = getattr(app_views, viewset_name)
    return True


def save_serializers_from_file(model: Type[Model]) -> bool:
    key = model_key(model)
    name = model._meta.object_name
    app_label = model._meta.app_label

    full_serializer = f"{name}Serializer"
    simple_serializer = f"{name}SimpleSerializer"
    export_serializer = f"{name}ExportSerializer"

    try:
        app_serializers = importlib.import_module(f"apps.{app_label}.serializers")

        if hasattr(app_serializers, full_serializer):
            FULL_SERIALIZERS[key] = getattr(app_serializers, full_serializer)
        if hasattr(app_serializers, simple_serializer):
            SIMPLE_SERIALIZERS[key] = getattr(app_serializers, simple_serializer)
        if hasattr(app_serializers, export_serializer):
            EXPORT_SERIALIZERS[key] = getattr(app_serializers, export_serializer)
    except ImportError:
        pass


# ── ViewSet creation (only runs once per model) ──────────────────────────────
def get_or_create_viewset(model: Type[Model]) -> Type[ModelViewSet]:
    key = model_key(model)
    if key not in VIEWSETS:
        save_viewsets_from_file(model)
    if key not in VIEWSETS:
        class_name = f"{model._meta.object_name}ViewSet"

        class DynamicViewSet(BaseProtectionViewSet):
            queryset = model._default_manager.all()
            serializer_model_name = model._meta.object_name

            # Optional dynamic extras
            ordering_fields = "__all__"
            ordering = "-id"

        VIEWSETS[key] = DynamicViewSet
        DynamicViewSet.__name__ = class_name  # nice for debug

    return VIEWSETS[key]


def get_or_create_import_export_viewset(model: Type[Model]) -> Type[ModelViewSet]:
    """Same routes as DynamicViewSet but CRUD endpoints return 404 (custom-api)."""
    key = f"ie-{model_key(model)}"
    if key not in IMPORT_EXPORT_VIEWSETS:
        qs = model._default_manager.all()

        class DynamicImportExportViewSet(ImportExportOnlyViewSet):
            queryset = qs
            serializer_model_name = model._meta.object_name
            ordering_fields = "__all__"
            ordering = "-id"

        DynamicImportExportViewSet.__name__ = (
            f"{model._meta.object_name}ImportExportViewSet"
        )
        IMPORT_EXPORT_VIEWSETS[key] = DynamicImportExportViewSet
    return IMPORT_EXPORT_VIEWSETS[key]


# ── Optional: Pre-generate everything at startup ─────────────────────────────
def pregenerate_all():
    """Call this once at startup to create all classes eagerly"""
    for app_config in apps.get_app_configs():
        if app_config.label in settings.EXCLUDE_APPS:
            continue
        for model in app_config.get_models():
            if model._meta.abstract or model._meta.proxy:
                continue
            save_serializers_from_file(model)
            save_viewsets_from_file(model)
            for serializer_type in ["full", "simple"]:
                get_or_create_serializer(model, serializer_type)
            get_or_create_viewset(model)
