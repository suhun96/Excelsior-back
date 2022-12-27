from django.urls import path

from companies.views import *


urlpatterns = [
    path('title-list', CustomTitleListView.as_view()),
    path('title-create', CustomTitleCreateView.as_view()),
    path('title-modify', CustomTitleModifyView.as_view()),
    path('value-create', CustomValueCreateView.as_view()),
    path('value-list', CustomValueListView.as_view()),
    path('value-modify', CustomValueModifyView.as_view())
]
