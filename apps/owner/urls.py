from django.urls import path, include

from apps.owner.views import SupportInformationView, SmsLogListView
from apps.owner.views import UserOwnerViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserOwnerViewSet, basename='owner-user')

app_name = "owner"

urlpatterns = [
    path("owner/support-information/", SupportInformationView.as_view(), name="owner-support"),
    path("owner/sms-logs/", SmsLogListView.as_view(), name="owner-sms-log"),
    path("owner/", include(router.urls)),
]
