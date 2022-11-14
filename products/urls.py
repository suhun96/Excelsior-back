from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('company', CompanyView.as_view()),
    path('company-etc', CompanyEtcView.as_view()),
    path('product-d1', ProductD1InfoView.as_view()),
    path('d2', ProductD2InfoView.as_view())
]

