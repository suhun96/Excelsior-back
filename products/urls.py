from django.urls import path

from products.views import *

urlpatterns = [
    path('group', CreateProductGroupView.as_view()),
    path('company', CreateCompanyView.as_view()),
    path('info', CreateProductInfoView.as_view()),
    path('inbound', CreateInboundOrderView.as_view()),
    path('outbound', CreateOutboundOrderView.as_view()),
    path('outbound_conf', ConfirmOutboundOrderView.as_view()),
]