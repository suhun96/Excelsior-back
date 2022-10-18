from turtle import position
from unicodedata import name
from django.views   import View
from django.http    import JsonResponse, HttpResponse
from django.conf    import settings

# Model
from users.models   import *

# View
class SignUpView(View):
    def post(self, request):
        data = request.POST
        try:
            new_user = User.objects.create(
                phone       = data.phone,
                name        = data.name,
                password    = data.phone,
                position    = data.position,
                admin       = 0, # True = 관리자 , False = 일반회원
                status      = 1  # True = 활성화 , False = 비활성화
            )

            check_user_info = list(User.objects.get(id = new_user.id)) 
            return JsonResponse({'message' : check_user_info }, status = 200)

        except:
            return JsonResponse({'message' : 'SignUpView Error'}, status = 403)
