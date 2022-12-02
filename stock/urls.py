from django.urls import path

from stock.views import * 

urlpatterns = [
    path('sheet', CreateInventorySheetView.as_view()),
    path('sheet-ins', InsertInventorySheetView.as_view()),
    path('list-price', ListProductPriceView.as_view()),
    path('list-quantity', ListProductQuantityView.as_view()),
    path('sheet-mod', ModifyInventorySheetView.as_view()),
    path('sheet-del', DeleteInventorySheetView.as_view())
]
