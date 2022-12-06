from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('group-mod', ModifyProductGroupView.as_view()),
    path('etc-title', ProductEtcTitleView.as_view()),
    path('etc-desc', ProductEtcDescView.as_view()),
    path('info',ProductInfoView.as_view()),
    path('mod', ModifyProductInfoView.as_view()),
    path('set-info', SetInfoView.as_view())
]

