import jwt
from django.views       import View
from django.http        import JsonResponse
from django.conf        import settings
from django.db          import transaction

from datetime       import datetime, timedelta

# Model
from users.models       import *
from users.decorator   import jwt_decoder

# View
class SignUpView(View):
    # @jwt_decoder
    def post(self, request):
        data = request.POST
        # user = request.user
        
        try:
            # if not user.admin == True:
            #     return JsonResponse({'messaga' : 'You do not have permission to create a member.'}, status = 403) 

            new_user , is_created = User.objects.get_or_create(
                phone = data['phone'],
                defaults = {
                'phone'       : data['phone'],
                'name'        : data['name'],
                'email'       : data['email'],
                'team'        : data['team'],
                'password'    : 1234,            # 기본 비밀번호
                'position'    : data['position'], 
                'admin'       : 1
                # admin  80 = 매니저  / 1 = 일반회원
                # status 기본적으로 True    / True = 활성화 , False = 비활성화  
                }
                )
                

            if not is_created:
                return JsonResponse({'messaga' : 'The phone number is already registered.'}, status = 403)
            
            check_user_info = list(User.objects.filter(id = new_user.id).values(
                "phone",
                "name",
                'email',
                'team', 
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
        user= request.user 
        UOF = User.objects.filter(id = user.id)
        
        try:
            with transaction.atomic():
                if len(modify_data) == 0:
                    return JsonResponse({'message' : 'No data contents to be modified.'}, status = 403)

                if "name" in modify_data:
                    UOF.update(name = modify_data['name'])

                if "password" in modify_data:
                    UOF.update(password = modify_data['password'])

                if "position" in modify_data:
                    UOF.update(position = modify_data['position'])


            return JsonResponse({'message' : 'Check update'}, status = 204)

        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 400)

class ChangeStatusView(View):
    @jwt_decoder
    def post(self, request):
        user = request.user
        data = request.POST
        change_id = data['id']
        
        try:
            if not user.admin == True:
                return JsonResponse({'message' :'You are an unauthorized user.'}, status = 403)
            
            User.objects.filter(id = change_id).update(status = 0)
            
            return JsonResponse({'message' : 'The user account has been stopped.'}, status = 204)
            
        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 400)

class UserListView(View):
    @jwt_decoder 
    def get(self, request):
        User_List = User.objects.all()
        admin_user = request.user

        user_list = [{
            'use_id'    : user.id, 
            'phone'     : user.phone,
            'name'      : user.name,
            'position'  : user.position,
            'status'    : user.status
        } for user in User_List]

        return JsonResponse({'user_list' : user_list} , status = 200)