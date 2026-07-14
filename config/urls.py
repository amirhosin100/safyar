from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.core.auto_generator.auto_generator import get_or_create_viewset
from apps.core.utils.api_route import get_crud_api_prefix
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

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


        except Exception as e:
            print(f"Skipping {app_config.label}.{model.__name__}: {e}")


version = "v1"

schema_urlpatterns = [
    path('', SpectacularAPIView.as_view(), name='schema'),
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"api/{version}/schema/", include(schema_urlpatterns)),
    path(f'api/{version}/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path(f"api/{version}/", include(router.urls)),
    path(f"api/{version}/", include("apps.owner.urls")),
    path(f"api/{version}/", include("apps.wallet.urls")),
    path(f"api/{version}/", include("apps.smoothing.urls")),
    path(f"api/{version}/", include("apps.account.urls")),
    path(f"api/{version}/", include("apps.project.urls")),
    path(f"api/{version}/", include("apps.costumer.urls",namespace="costumer")),
    path(f"api/{version}/", include("apps.report.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
