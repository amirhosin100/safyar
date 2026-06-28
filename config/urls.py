from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.core.auto_generator.auto_generator import get_or_create_import_export_viewset, get_or_create_viewset
from apps.core.utils.api_route import get_crud_api_prefix

router = DefaultRouter()
custom_import_export_router = DefaultRouter()

for app_config in apps.get_app_configs():
    if app_config.label in settings.EXCLUDE_APPS:
        continue

    for model in app_config.get_models():
        if model._meta.abstract or model._meta.proxy:
            continue
        if model.__name__ in settings.EXCLUDE_MODELS:
            continue

        try:
            viewset_class = get_or_create_viewset(model)

            prefix = get_crud_api_prefix(model)
            basename = f"{app_config.label}-{model._meta.model_name}"
            router.register(prefix, viewset_class, basename=basename)

            ie_viewset_class = get_or_create_import_export_viewset(model)
            custom_import_export_router.register(
                prefix,
                ie_viewset_class,
                basename=f"custom-{basename}",
            )

        except Exception as e:
            print(f"Skipping {app_config.label}.{model.__name__}: {e}")

# Django auth.Group CRUD (auth app is excluded from auto-registration)
try:
    group_prefix = get_crud_api_prefix(Group)
    router.register(
        group_prefix,
        get_or_create_viewset(Group),
        basename="auth-group",
    )
    custom_import_export_router.register(
        group_prefix,
        get_or_create_import_export_viewset(Group),
        basename="custom-auth-group",
    )
except Exception as e:
    print(f"Skipping auth.Group registration: {e}")

version = "v1"
urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"api/{version}/", include(router.urls)),
    path(f"api/{version}/",include("apps.owner.urls")),
    path(f"api/{version}/",include("apps.wallet.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
