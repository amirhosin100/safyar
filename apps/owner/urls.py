from django.urls import path, include
from apps.owner.views import SupportInformationView
from apps.owner.views import UserOwnerViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserOwnerViewSet, basename='owner-user')

app_name = "owner"

urlpatterns = [
    path("owner/support-information/", SupportInformationView.as_view(), name="owner-support"),
    path("owner/", include(router.urls)),
]
