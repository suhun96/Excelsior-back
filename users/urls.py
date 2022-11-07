from django.urls import path

from users.views import *

urlpatterns = [
    path('signup', SignUpView.as_view()),
    path('signin', SignInView.as_view()),
    path('modify', ModifyView.as_view()),
<<<<<<< HEAD
    path('pause', ChangeStatusView.as_view()),
    path('my',UserInfoView.as_view())
=======
    path('per', PermissionSignUpView.as_view()),
    path('',UserInfoView.as_view())
>>>>>>> origin
]