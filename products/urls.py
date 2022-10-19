from django.urls import path

from products.views import *

urlpatterns = [
    path('create/pg', CreateProductGroupView.as_view()),
]