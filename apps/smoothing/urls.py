from django.urls import path
from apps.smoothing.views import SmoothingAPIView, BranchAPIView

app_name = "smoothing"

urlpatterns = [
    path("smoothing/user/smoothing/", SmoothingAPIView.as_view(), name="user-smoothing"),
    path("smoothing/user/branch/", BranchAPIView.as_view(), name="branch-smoothing"),

]
