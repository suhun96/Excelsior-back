from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('etc-title', ProductEtcTitle.as_view()),
    path('etc-desc', ProductEtcDesc.as_view()),
    path('d1', ProductD1InfoView.as_view()),
    path('d2', ProductD2InfoView.as_view()),
    path('d3', ProductD3InfoView.as_view())
]

