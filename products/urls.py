from django.urls import path

from products.views import *

urlpatterns = [
    path('create/pg', CreateProductGroupView.as_view()),
    path('create/cp', CreateCompanyView.as_view()),
    path('create/product', CreateProductView.as_view()),
    path('update/product', UpdateProductView.as_view()),
]