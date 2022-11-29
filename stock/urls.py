from django.urls import path

from stock.views import * 

urlpatterns = [
    path('check', CreateInventorySheetView.as_view()),
    path('list-price', ListProductPriceView.as_view()),
    path('list-quantity', ListProductQuantityView.as_view()),
    path('check-mod', ModifyInventorySheetView.as_view())
    
]
