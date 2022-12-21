import jwt, bcrypt ,re

from django.shortcuts   import render
from django.views       import View
from django.http        import JsonResponse , HttpResponse
from django.conf        import settings
from django.db          import transaction

from datetime           import datetime, timedelta

# Model
from users.models       import *
from users.decorator    import jwt_decoder

# Swagger
from drf_yasg.utils     import swagger_auto_schema

# View
class SignUpView(View):
    @swagger_auto_schema
    def post(self, request):
        data = request.POST

        # 정규식 : 전화번호, 비밀번호
        REGEX_PHONE = '(010)\d{4}\d{4}'                          # 010 휴대전화 정규표현식
        REGEX_PW    = '^(?=.{8,16}$)(?=.*[a-z])(?=.*[0-9]).*$'   # 비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 
        
        # bcrypt
        new_salt = bcrypt.gensalt()
        bytes_password = data['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(bytes_password, new_salt)

        try:
            with transaction.atomic():

                # 전화번호 형식 확인
                if not re.fullmatch(REGEX_PHONE, data['phone']):
                    return JsonResponse({'message' : '010-XXXX-XXXX 형식을 따라주세요.'}, status = 403)
                
                # 패스워드 형식 확인
                if not re.fullmatch(REGEX_PW, data['password']):
                    return JsonResponse({'message' : '비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 '}, status = 403)

                CREATE_SET = {'admin' : False, 'status' : False}

                for key, value in data.items():
                    if key in ['phone', 'name', 'email', 'team', 'position']:
                        CREATE_SET.update({key : value})
                    
                    
                    elif key == 'password':
                        CREATE_SET.update({key : hashed_password.decode('utf-8')})
                    
                    # else:
                    #     raise KeyError

                new_user , is_created = User.objects.get_or_create(
                    phone = data['phone'],
                    defaults = {**CREATE_SET})
                    # admin  False / status 기본적으로 True (True = 활성화 , False = 비활성화) 

                if not is_created:
                    return JsonResponse({'message' : 'The phone number is already registered.'}, status = 403)
                
                check_user_info = list(User.objects.filter(id = new_user.id).values()) 
                
            return JsonResponse({'message' : check_user_info }, status = 200)
        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'})

class PermissionSignUpView(View):
    @jwt_decoder
    def post(self, request):
        user = request.user
        input_data = request.POST

        try:
            with transaction.atomic():

                if user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)

                if input_data['status'] == "False":
                    User.objects.filter( phone = input_data['phone']).update( status = False)
                    return JsonResponse({'message' : '사용이 허가 되었습니다'}, status = 200)
                
                if input_data['status'] == "True": 
                    User.objects.filter( phone = input_data['phone']).update( status = True)
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

            if user.exists() == False:
                return JsonResponse({'Message' : 'The mobile phone number you entered does not exist.'}, status = 402)
            
            try_user = User.objects.get(phone = signin_data['phone'])

            if try_user.status == False:
                return JsonResponse({'message' : '관리자에게 계정 허가를 요청하세요.'}, status = 403)

            if bcrypt.checkpw(input_pw.encode('utf-8'), try_user.password.encode('utf-8') ) == False:
                return JsonResponse({'Message' : 'Please check the password.'}, status = 402)
            
            jwt_token = self.create_jwt_token(try_user.id , try_user.admin)
            
            return JsonResponse({'message' : jwt_token }, status = 200)
        except Exception as e:
            return JsonResponse({'message' : e} , status = 400)

class CheckPasswordView(View):
    @jwt_decoder
    def post(self, request):
        input_password = request.POST['password']
        user = request.user
        try_user_password = User.objects.get(id = user.id).password
        if bcrypt.checkpw(input_password.encode('utf-8'), try_user_password.encode('utf-8')) == False:
            return JsonResponse({'message' : 'no'}, status = 400)

        return JsonResponse({'message' : 'ok' }, status = 200)

class AdminModifyView(View):
    @jwt_decoder
    def post(self, request):
        modify_user = request.GET.get('phone',None)
        modify_data = request.POST
        user = request.user

        # bcrypt
        new_salt = bcrypt.gensalt()
        # 정규식
        REGEX_PW    = '^(?=.{8,16}$)(?=.*[a-z])(?=.*[0-9]).*$'   # 비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 
        
        if User.objects.get(id = user.id).admin == False:
            return JsonResponse({'message' : '권한이 없는 요청입니다.'}, status = 400)

        if not User.objects.filter(phone = modify_user).exists():
            return JsonResponse({'message' : '유저가 존재하지 않는 요청입니다.'}, status = 400)

        try:
            with transaction.atomic():
                UPDATE_SET = {}
                # key_check_list = ['phone', 'name', 'email', 'team', 'position'] 
                key_check_list = ['name', 'email', 'team', 'position'] 

                

                for key, value in modify_data.items():
                    # key 값이 'password'일 경우, 정규식과 입력된 비밀번호 비교
                    # if key == 'phone':
                    #     if User.objects.filter(phone = value).exists():
                    #         return JsonResponse({'message' : '이미 존재하는 휴대폰 번호 입니다.'}, status = 403)
                    #     else:
                    #         UPDATE_SET.update({key : value})

                    if key == 'password':
                        if not re.fullmatch(REGEX_PW, value):
                            return JsonResponse({'message' : '비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 '}, status = 403)
                        # 비밀번호 decode 후 저장.
                        hashed_password = bcrypt.hashpw(value.encode('utf-8'), new_salt)
                        UPDATE_SET.update({key : hashed_password.decode('utf-8')})

                    elif key in key_check_list:
                        UPDATE_SET.update({key : value})
                    
                    # else:
                    #     JsonResponse({'message' : '존재하지 않는 키값입니다.'}, status = 403)                        
                # 변경 사항 업데이트
                User.objects.filter(phone = modify_user).update(**UPDATE_SET)
                return JsonResponse({'message' : 'check update'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항이 발생했습니다.'}, status = 400)

class UserModifyView(View):
    @jwt_decoder
    def post(self, request):
        modify_data = request.POST
        user= request.user 
                
        # 정규식
        REGEX_PHONE = '(010)\d{4}\d{4}' 
        REGEX_PW    = '^(?=.{8,16}$)(?=.*[a-z])(?=.*[0-9]).*$'   # 비밀번호 정규표현식, 8자 이상 16자 이하, 소문자, 숫자 최소 하나 사용 
        
        UPDATE_OPT = ['phone', 'name', 'email', 'password', 'position']
        UPDATE_SET = {}

        try:
            if 'phone' in modify_data:
                if re.fullmatch(REGEX_PHONE, modify_data['phone']) == False:
                    return JsonResponse({'message' : '핸드폰 번호 형식을 지켜주세요'}, status = 403)
            
            # bcrypt
            if 'password' in modify_data:
                new_salt = bcrypt.gensalt()
                bytes_password = modify_data['password'].encode('utf-8')
                hashed_password = bcrypt.hashpw(bytes_password, new_salt)
                
                if re.fullmatch(REGEX_PW, modify_data['password']) == False:
                    return JsonResponse({'message' : '비밀 번호 형식을 지켜주세요'}, status = 403)

            with transaction.atomic():
                for key, value in modify_data.items():
                    if key in UPDATE_OPT:
                        if key == 'password':
                            UPDATE_SET.update({key : hashed_password.decode('utf-8') })
                        else:
                            UPDATE_SET.update({key : value})

                    # else:
                    #     return JsonResponse({'message' : f'{key} 수정할 수 없는 키값이 들어왔습니다'})

                User.objects.filter(id =user.id).update(**UPDATE_SET)
                after = list(User.objects.filter(id = user.id).values('phone', 'name', 'email', 'team', 'position'))
            
            return JsonResponse({'message' : after}, status = 200)

        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 400)

class TotalUserListView(View):
    @jwt_decoder 
    def get(self, request):
        user = request.user
        
        try:
            if User.objects.filter(id = user.id, status = True ).exists() == False:
                return JsonResponse({'message' : "존재하지 않는 유저로부터 요청이 왔습니다."}, status = 403)

            else:
                user_list = list(User.objects.all().values(
                    'phone',     
                    'name',     
                    'email',  
                    'team',      
                    'position',  
                    'admin',     
                    'status',    
                    'created_at',
                    'updated_at'
                ))
            return JsonResponse({'user_list' : user_list} , status = 200)
        except:  
            return JsonResponse({'message' : '예외 사항 발생'} , status = 403)

class UserMyInfoView(View):
    @jwt_decoder
    def get(self, request):
        user = request.user
        
        try:
            if User.objects.filter(id = user.id, status = True ).exists() == False:
                return JsonResponse({'message' : "존재하지 않는 유저로부터 요청이 왔습니다."}, status = 403)

            user_info = list(User.objects.filter(id = user.id).values())
            
            return JsonResponse({'user_info' : user_info}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항 발생"}, status = 403)

class HealthCheckView(View):
    def health(request):
        return JsonResponse({"message" : "Hello world"}, status =200)