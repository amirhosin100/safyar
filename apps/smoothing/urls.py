from django.urls import path
from apps.smoothing.views import SmoothingAPIView, BranchAPIView

app_name = "smoothing"

urlpatterns = [
    path("smoothing/settings/smoothing/", SmoothingAPIView.as_view(), name="user-smoothing"),
    path("smoothing/settings/branch/", BranchAPIView.as_view(), name="branch-smoothing"),

]
