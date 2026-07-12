from apps.costumer.views import AddCostumerView
from django.urls import path

app_name = 'costumer'

urlpatterns = [
    path("costumer/add-costumer/", AddCostumerView.as_view(), name="add_costumer"),
]

