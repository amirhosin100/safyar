"""
ViewSet exposing only Excel import/export (no CRUD routes that resolve).
Registered under /v1/custom-api/ separately from full CRUD.
"""

from rest_framework.exceptions import NotFound
from apps.core.base_classes.base_viewset import (BaseProtectionViewSet)


class ImportExportOnlyViewSet(BaseProtectionViewSet):
    """Blocks standard CRUD; keeps export/import and shared queryset/filter stack."""

    def list(self, request, *args, **kwargs):
        raise NotFound()

    def create(self, request, *args, **kwargs):
        raise NotFound()

    def retrieve(self, request, *args, **kwargs):
        raise NotFound()

    def update(self, request, *args, **kwargs):
        raise NotFound()

    def partial_update(self, request, *args, **kwargs):
        raise NotFound()

    def destroy(self, request, *args, **kwargs):
        raise NotFound()

    def form_schema(self, request, *args, **kwargs):
        raise NotFound()
