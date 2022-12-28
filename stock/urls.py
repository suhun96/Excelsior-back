from django.urls import path

from stock.views import * 

urlpatterns = [
    path('sheet', CreateSheetView.as_view()),
    path('list', QunatityByWarehouseView.as_view()),
    path('sheet-list', SheetListView.as_view()),  # 쿼리 파라미터 type으로 필터링 가능('inbound', 'outbound)
    path('sheet-detail', ClickSheetView.as_view()), #  쿼리 파라미터 sheet_id 필요합니다
    path('sheet-info', InfoSheetListView.as_view()),
    path('quantity', TotalQuantityView.as_view()),
    path('price', PriceCheckView.as_view()),
    path('serial-check', SerialCodeCheckView.as_view()),
    path('serial-tracking', SerialActionHistoryView.as_view()),
    path('stock-info', StockTotalView.as_view()),
    path('sheet-modify', ModifySheetView.as_view()), # POST
    path('sheet-delete', DeleteSheetView.as_view()), # POST 
    path('sheet-log-list', InquireSheetLogView.as_view()), # GET
]
