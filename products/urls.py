from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('company', CompanyView.as_view()),
    path('company-etc-title', CompanyEtcTitleView.as_view()),
    path('company-etc-desc', CompanyEtcDescView.as_view()),
    path('company-ph', CompanyPhonebookView.as_view()),
    path('d1', ProductD1InfoView.as_view()),
    path('d2', ProductD2InfoView.as_view()),
    path('d3', ProductD3InfoView.as_view())
]

