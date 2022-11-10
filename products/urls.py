from django.urls import path

from products.views import *


urlpatterns = [
    path('group', ProductGroupView.as_view()),
    path('company', CompanyView.as_view()),
    path('comp', ComponentInfoView.as_view()),
    path('bom', BomInfoView.as_view())
]

