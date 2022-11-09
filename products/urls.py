from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('company', CompanyView.as_view()),
    # path('info', CreateProductInfoView.as_view()),
    # path('inbound', CreateInboundOrderView.as_view()),
    # path('outbound', CreateOutboundOrderView.as_view()),
    # path('outbound_conf', ConfirmOutboundOrderView.as_view()),
    # path('setinfo',CreateSetInfoView.as_view()),
    # path('print', PrintProductBarcodeView.as_view())
]

