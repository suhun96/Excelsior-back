from django.urls import path

from stock.views import * 

urlpatterns = [
    path('title-create', CreateSerialCodeTitleView.as_view()), # POST / Form-data
    path('title-modify', ModifySerialCodeTitleView.as_view()), # POST / Form-data
    path('title-list',   InquireSerialCodeTitleView.as_view()), # GET / Query-parameter
    path('value-create', CreateSerialCodeValueView.as_view()), # POST / Form-data
    path('check', SerialCodeCheckView.as_view()),
    path('code-list', InquireSerialCodeView.as_view()),
]