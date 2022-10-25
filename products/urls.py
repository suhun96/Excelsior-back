from django.urls import path

from products.views import *

urlpatterns = [
    path('create/pg', CreateProductGroupView.as_view()),
    path('create/cp', CreateCompanyView.as_view()),
    path('create/product', CreateProductInfoView.as_view()),
    path('create/order', CreateInboundOrderView.as_view()),
]