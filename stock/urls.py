from django.urls import path

from stock.views import * 

urlpatterns = [
    path('sheet', CreateSheetView.as_view()),
]
