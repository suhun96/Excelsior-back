import jwt, bcrypt ,re

from django.views       import View
from django.http        import JsonResponse 
from django.conf        import settings
from django.db          import transaction

from datetime           import datetime, timedelta

# Model
from users.models       import *
from users.decorator    import jwt_decoder

# View
class SignUpView(View):
    def post(self, request):
        data = request.POST
        password = data['password']

        # 정규식 : 전화번호, 비밀번호
        REGEX_PHONE = '(010)\d{4}\d{4}'                          # 010 휴대전화 정규표현식
        REGEX_PW    = '^(?=.{8,16}$)(?=.*[a-z])(?=.*[0-9]).*$'   # 비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 
        
        # bcrypt
        new_salt = bcrypt.gensalt()
        bytes_password = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(bytes_password, new_salt)

        try:
            with transaction.atomic():

                # 전화번호 형식 확인
                if not re.fullmatch(REGEX_PHONE, data['phone']):
                    return JsonResponse({'message' : '010XXXXXXXX 형식을 따라주세요.'}, status = 403)
                
                # 패스워드 형식 확인
                if not re.fullmatch(REGEX_PW, password):
                    return JsonResponse({'message' : '비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 '}, status = 403)

                new_user , is_created = User.objects.get_or_create(
                    phone = data['phone'],
                    defaults = {
                    'phone'       : data['phone'],
                    'name'        : data['name'],
                    'email'       : data['email'],
                    'team'        : data['team'],
                    'password'    : hashed_password.decode('utf-8'),    # 기본 비밀번호
                    'position'    : data['position'], 
                    # admin  False / status 기본적으로 True (True = 활성화 , False = 비활성화)  
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
        except Exception:
            return JsonResponse({'message' : 'qwdf 예외 사항이 발생해서 트랜잭션을 중지했습니다.'})

class PermissionSignUpView(View):
    @jwt_decoder
    def post(self, request):
        user = request.user
        input_data = request.POST

        try:
            with transaction.atomic():

                if not user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)

                if User.objects.get(id = input_data['id']).status == False:
                    User.objects.filter( id = input_data['id']).update( status = True)
                    return JsonResponse({'message' : '사용이 허가 되었습니다'}, status = 200)
                else:
                    User.objects.filter( id = input_data['id']).update( status = False )
                    return JsonResponse({'message' : '사용이 불허 되었습니다.'}, status = 200)
        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'}, status = 403)



class SignInView(View):
    def create_jwt_token(self, user_id, user_admin):
        jwt_token = jwt.encode({'user_id' : user_id , 'admin' : user_admin, 'exp':datetime.utcnow() + timedelta(days = 3)}, settings.SECRET_KEY, settings.ALGORITHM)

        return jwt_token

    def post(self, request):
        signin_data = request.POST
        input_pw = signin_data['password']
        user = User.objects.filter(phone = signin_data['phone'])
        try:
            if not user.exists() == True:
                return JsonResponse({'Message' : 'The mobile phone number you entered does not exist.'}, status = 402)
            
            try_user = User.objects.get(phone = signin_data['phone'])
        
            if bcrypt.checkpw(input_pw.encode('utf-8'), try_user.password.encode('utf-8') ) == False:
                return JsonResponse({'Message' : 'Please check the password.'}, status = 402)
            
            jwt_token = self.create_jwt_token(try_user.id , try_user.admin)
            
            return JsonResponse({'message' : jwt_token }, status = 200)
        except Exception as e:
            return JsonResponse({'message' : e} , status = 400)

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

class UserInfoView(View):
    @jwt_decoder
    def get(self, request):
        user = request.user
        user_info = User.objects.get(id = user.id)

        user_info = {
            'phone' : user_info.phone,
            'name'  : user_info.name,
            'email' : user_info.email,
            'team'  : user_info.team,
            'position' : user_info.position
        }
        
        return JsonResponse({'user_info' : user_info}, status = 200)