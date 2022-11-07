from django.urls import path

from users.views import *

urlpatterns = [
    path('signup', SignUpView.as_view()),
    path('signin', SignInView.as_view()),
    path('modify', ModifyView.as_view()),
    path('pause', ChangeStatusView.as_view()),
    path('',UserInfoView.as_view())
]