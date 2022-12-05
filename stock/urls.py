from django.urls import path

from stock.views import * 

urlpatterns = [
    path('sheet', NomalStockView.as_view()),
    path('list', QunatityByWarehouseView.as_view())
]
