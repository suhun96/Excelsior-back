from django.urls import path, include

from stock.views import * 

urlpatterns = [
    path('sheet', CreateSheetView.as_view()),
    path('list', QunatityByWarehouseView.as_view()),
    path('sheet-list', SheetListView.as_view()),  # 쿼리 파라미터 type으로 필터링 가능('inbound', 'outbound)
    path('sheet-detail', ClickSheetView.as_view()), #  쿼리 파라미터 sheet_id 필요합니다
    path('sheet-info', InfoSheetListView.as_view()),
    path('quantity', TotalQuantityView.as_view()),
    path('price', PriceCheckView.as_view()),
    path('stock-info', StockTotalView.as_view()),
    path('sheet-modify', ModifySheetView.as_view()), # POST
    path('sheet-delete', DeleteSheetView.as_view()), # POST 
    path('sheet-etc-modify', ModifySheetEtcView.as_view()), # POST
    path('sheet-etc', GetSheetEtcView.as_view()), # GET 
    path('sheet-log-list', InquireSheetLogView.as_view()), # GET
    path('serial/', include('stock.urls_serial_code')),
    path('check-set', CheckSetProductView.as_view()),
    path('generate-set', GenerateSetProductView.as_view()),
    path('modify-custom-price', ModifyMovingAverageMethodView.as_view()),
    path('sheet-log', InquireSheetLogView.as_view()),
    path('serial-code-log', InquireSerialLogView.as_view()),
    path('query-test', QueryTestView.as_view())
]
