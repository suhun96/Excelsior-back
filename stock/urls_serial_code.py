from django.urls import path

from stock.views import * 

urlpatterns = [
    path('title-create', CreateSerialCodeTitleView.as_view()), # POST / Form-data
    path('title-modify', ModifySerialCodeTitleView.as_view()), # POST / Form-data
    path('title-list',   InquireSerialCodeTitleView.as_view()), # GET / Query-parameter
    path('value-create', CreateSerialCodeValueView.as_view()), # POST / Form-data
    path('value-delete', DeleteSerialCodeValueView.as_view()),
    path('check', SerialCodeCheckView.as_view()),
    path('code-list', InquireSerialCodeView.as_view()),
    path('set-code-list', InquireSetSerialCodeView.as_view()),
    path('set-decompose', DecomposeSetSerialCodeView.as_view())
]