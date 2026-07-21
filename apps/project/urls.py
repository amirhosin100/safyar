from django.urls import path
from apps.project.views import (
    MainPartListView,
    ProjectScheduleListView,
    AccessProjectView
)

app_name = 'project'

urlpatterns = [
    path("project/main-parts/", MainPartListView.as_view(), name="main-parts"),
    path("project/schedules/", ProjectScheduleListView.as_view(), name="schedules"),
    path("project/access/",AccessProjectView.as_view(), name="access"),
]
