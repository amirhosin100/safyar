from django.urls import path
from apps.smoothing.views import SmoothingAPIView, BranchAPIView, SendBulkSMSAPIView, SendSingleSMSAPIView

app_name = "smoothing"

urlpatterns = [
    path("smoothing/settings/smoothing/", SmoothingAPIView.as_view(), name="user-smoothing"),
    path("smoothing/settings/branch/", BranchAPIView.as_view(), name="branch-smoothing"),
    path("smoothing/sms/bulk/", SendBulkSMSAPIView.as_view(), name="send-bulk-sms"),
    path("smoothing/sms/single/<int:costumer_id>/", SendSingleSMSAPIView.as_view(), name="send-single-sms"),

]
