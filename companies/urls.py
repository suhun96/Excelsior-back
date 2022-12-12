from django.urls import path

from companies.views import *


urlpatterns = [
    path('info', CompanyView.as_view()),
    path('mod', CompanyModifyView.as_view()),
    path('etc-title', CompanyEtcTitleView.as_view()),
    path('etc-desc', CompanyEtcDescView.as_view()),
    path('contacts', CompanyPhonebookView.as_view()),
    path('status', CompnayStatusView.as_view())
]

