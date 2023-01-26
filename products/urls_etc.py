from django.urls import path

from products.views import *


urlpatterns = [
    path('title-list', InquireProductEtcTitleView.as_view()),
    path('title-create', CreateProductEtcTitleView.as_view()),
    path('title-modify', ModifyProductEtcTitleView.as_view()),
    path('desc-create', CreateProductEtcDescView.as_view()),
    path('desc-list', InquireProductEtcDescView.as_view()),
]