import jwt
from django.views   import View
from django.http    import JsonResponse
from django.conf    import settings

from datetime       import datetime, timedelta

# Model
from users.models       import *
from users.jwtdecoder   import jwt_decoder

# View
class SignUpView(View):
    @jwt_decoder
    def post(self, request):
        data = request.POST
        user = request.user
        
        try:
            if not user.admin == True:
                return JsonResponse({'messaga' : 'You do not have permission to create a member.'}, status = 403) 

            new_user , is_created = User.objects.get_or_create(
                phone = data['phone'],
                defaults = {
                'phone'       : data['phone'],
                'name'        : data['name'],
                'password'    : 1234,            # 기본 비밀번호
                'position'    : data['position'] 
                # admin  기본적으로 False   / True = 관리자 , False = 일반회원
                # status 기본적으로 True    / True = 활성화 , False = 비활성화      
            })

            if not is_created:
                return JsonResponse({'messaga' : 'The phone number is already registered.'}, status = 403)
            
            check_user_info = list(User.objects.filter(id = new_user.id).values(
                "phone",
                "name",
                "password",
                "position",
                "admin",
                "status"
            )) 
            
            return JsonResponse({'message' : check_user_info }, status = 200)

        except:
            return JsonResponse(status = 403)

class SignInView(View):
    def create_jwt_token(self, user_id, user_admin):
        jwt_token = jwt.encode({'user_id' : user_id , 'admin' : user_admin, 'exp':datetime.utcnow() + timedelta(days = 3)}, settings.SECRET_KEY, settings.ALGORITHM)

        return jwt_token

    def post(self, request):
        signin_data = request.POST
        
        try:
            if not User.objects.filter(phone = signin_data['phone']).exists() == True:
                return JsonResponse({'Message' : 'The mobile phone number you entered does not exist.'}, status = 402)
            
            get_user_info = User.objects.get(phone = signin_data['phone'])
            
            if not get_user_info.password == signin_data['password']:
                return JsonResponse({'Message' : 'Please check the password.'}, status = 402)
            
            jwt_token = self.create_jwt_token(get_user_info.id, get_user_info.admin)
            
            return JsonResponse({'message' : jwt_token }, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 400)

class ModifyView(View):
    @jwt_decoder
    def post(self, request):
        modify_data = request.POST
        user = request.user
        try:
            modify_user_info = User.objects.filter(id = user.id)
            
            return

        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 400)
