from django.urls import path

from locations.views import *

urlpatterns = [
    path('property', CreateWarehousePropertyView.as_view()),
    path('property-modify', ModifyWarehousePropertyView.as_view()),
    path('property-delete', DeleteWarehousePropertyView.as_view()),
    
    path('type', CreateWarehouseTypeView.as_view()),
    path('type-modify', ModifyWarehouseTypeView.as_view()),
    path('type-delete', DeleteWarehouseTypeView.as_view()),
    
    path('info',WarehouseInfoView.as_view()),
    path('status', WarehouseStatusView.as_view()),
    path('main', SetMainWarehouseView.as_view())
]