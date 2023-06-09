from django.urls import path, include

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('group-mod', ModifyProductGroupView.as_view()),
    path('info',ProductInfoView.as_view()),
    path('mod', ModifyProductInfoView.as_view()),
    path('set-info', SetInfoView.as_view()),
    path('status', ProductStatusView.as_view()),
    path('group-status', ProductGroupStatusView.as_view()),
    path('etc/', include('products.urls_etc'))
]

