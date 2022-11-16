from django.urls import path

from locations.views import *

urlpatterns = [
    path('property', CreateWarehousePropertyView.as_view()),
    path('type', CreateWarehouseTypeView.as_view()),
    path('',WarehouseInfoView.as_view())
]