from django.urls import path

from stock.views import * 

urlpatterns = [
    path('inbound', ProductInboundView.as_view())
]
