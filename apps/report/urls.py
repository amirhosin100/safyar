from django.urls import path

from apps.report.views import (
    BranchCarCountView,
    SmoothingWalletTransactionReportView,
    SmoothingUserReportView,
    BranchColleagueReportView,
    GlobalReportView,
    BranchCostumerReportView,
    SmoothingBranchReportView,
)

app_name = "report"

urlpatterns = [
    path("report/branch/cars/", BranchCarCountView.as_view(), name="branch-car-count"),
    path("report/smoothing/transactions/", SmoothingWalletTransactionReportView.as_view(), name="smoothing-transactions"),
    path("report/smoothing/users/", SmoothingUserReportView.as_view(), name="smoothing-users"),
    path("report/branch/colleagues/", BranchColleagueReportView.as_view(), name="branch-colleagues"),
    path("report/global/", GlobalReportView.as_view(), name="global-report"),
    path("report/branch/costumers/", BranchCostumerReportView.as_view(), name="branch-costumers"),
    path("report/smoothing/branches/", SmoothingBranchReportView.as_view(), name="smoothing-branches"),
]