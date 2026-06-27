from django.urls import path
from apps.owner.views import SupportInformationView

app_name = "owner"

urlpatterns = [
    path("owner/support-information/", SupportInformationView.as_view(), name="owner-support")
]
