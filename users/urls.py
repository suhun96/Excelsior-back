from django.urls import path

from users.views import *

urlpatterns = [
    path('',UserMyInfoView.as_view()),
    path('signup', SignUpView.as_view()),
    path('signin', SignInView.as_view()),
    path('modify-user', UserModifyView.as_view()),
    path('modify-admin', AdminModifyView.as_view()),
    path('per', PermissionSignUpView.as_view()),
    path('check', CheckPasswordView.as_view()),
    path('list', TotalUserListView.as_view() )
]