from django.urls import path

from stock.views import * 

urlpatterns = [
    path('inbound', ProductInboundView.as_view()),
    path('outbound', ProductOutboundView.as_view()),
    path('list-price', ListProductPriceView.as_view()),
    path('list-quantity', ListProductQuantityView.as_view()),
    path('list-warehouse', ListProductWarehouseView.as_view())
]
