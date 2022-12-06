from django.urls import path

from stock.views import * 

urlpatterns = [
    path('sheet', NomalStockView.as_view()),
    path('list', QunatityByWarehouseView.as_view()),
    path('sheet-list', SheetListView.as_view()),  # 쿼리 파라미터 type으로 필터링 가능('inbound', 'outbound)
    path('sheet-click', ClickSheetView.as_view()) #  쿼리 파라미터 sheet_id 필요합니다
]
