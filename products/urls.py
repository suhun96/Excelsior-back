from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('group-mod', ModifyProductGroupView.as_view()),
    path('etc-title', ProductEtcTitleView.as_view()),
    path('etc-desc', ProductEtcDescView.as_view()),
    path('',ProductInfoView.as_view()),
    path('mod', ModifyProductInfoView.as_view())
]

