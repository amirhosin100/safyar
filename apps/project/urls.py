from django.urls import path
from apps.project.views import (
    MainPartListView,
)

app_name = 'project'

urlpatterns = [
    path("project/main-parts/", MainPartListView.as_view(), name="main-parts"),
]


