from django.urls import path

from companies.views import *


urlpatterns = [
    path('list', InquireCompanyPhonebookView.as_view()),
    path('register', CreateCompanyPhonebookView.as_view()),
    path('modify', ModifyCompanyPhonebookView.as_view()),
    path('delete', DeleteCompanyPhonebookView.as_view()),
]
