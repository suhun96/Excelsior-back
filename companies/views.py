import re

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection
from django.db.models   import Q
from django.utils       import timezone  

# Model
from users.models       import *
from products.models    import *
from companies.models   import *

# decorator & utills 
from users.decorator    import jwt_decoder
from products.utils     import *


class CompanyView(View):
    def get(self, request):
        
        filter_options = {
            'name'     : 'name__icontains',
            'keyword'  : 'keyword__icontains',
            'code'     : 'code__icontains',
            'represent': 'represent__icontains',
            'biz_no'   : 'biz_no__icontains',
            'biz_type' : 'biz_type__icontains',
            'biz_item' : 'biz_item__icontains',
            'phone'    : 'phone__icontains',
            'fax'      : 'fax__icontains',
            'mobile'   : 'mobile__icontains',
            'email'    : 'email__icontains',
            'address_main' : 'address_main__icontains',
            'address_desc' : 'address_desc__icontains',
            'zip_code' : 'zip_code__icontains'
        }

        filter_set = { filter_options.get(key) : value for (key, value) in request.GET.items() if filter_options.get(key) }
        
        result = list(Company.objects.filter(**filter_set).values())

        return JsonResponse({'message' : result} , status = 200)

    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        try:
            with transaction.atomic():
                # 필수값 (이름, 코드, 번호)이 있는지 확인 없으면 에러 발생.
                if not "name" in input_data:
                    return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)
                
                create_options = ['name','code','keyword','represent','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

                REGEX_CODE = '[A-Z]{2}'  

                CREATE_SET = {}

                # create_options 로 request.POST 의 키값이 정확한지 확인.
                for key in dict(request.POST).keys():
                    if key == 'name':
                        if Company.objects.filter(name = request.POST[key]) == True:
                            return JsonResponse({'message' : '회사 이름이 존재합니다.'}, status = 403)
                        
                        CREATE_SET.update({ key : request.POST[key] }) 
                    
                    if key == 'code':
                        if not re.fullmatch(REGEX_CODE, input_data['code']):
                            return JsonResponse({'message' : '회사 코드 형식을 확인해주세요. [A-Z] 2자리 '}, status = 403)

                        if Company.objects.filter(code = input_data['code']).exists():
                            return JsonResponse({'message' : '회사 코드가 이미 존재합니다.'}, status = 403)
                        
                        CREATE_SET.update({ key : request.POST[key] }) 

                    elif key in create_options:
                        
                        CREATE_SET.update({ key : request.POST[key] })
                    else:
                        return JsonResponse({'message' : '잘못된 키값이 들어오고 있습니다.'}, status = 403)
        
                
                new_company = Company.objects.create(**CREATE_SET)

                check_created = list(Company.objects.filter(id = new_company.id).values())

            return JsonResponse({'message' : check_created}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class CreateCompanyPhonebookView(View):
    def post(self, request):
        company_id = request.POST['company_id']

        CREATE_SET = {'company_id' : company_id}

        for key, value in request.POST.items():
            if key == 'name':
                CREATE_SET.update({key : value})
            if key == 'mobile':
                CREATE_SET.update({key : value})
            if key == 'email':
                CREATE_SET.update({key : value})

        new_company_phonebook = CompanyPhonebook.objects.create(**CREATE_SET)

        return JsonResponse({'message' : '새로운 연락처가 등록되었습니다.'}, status = 200)

class ModifyCompanyPhonebookView(View):
    def post(self, request):
        id = request.POST['company_phonebook_id']

        UPDATE_SET = {}

        for key, value in request.POST.items():
            if key == 'name':
                UPDATE_SET.update({key : value})
            if key == 'mobile':
                UPDATE_SET.update({key : value})
            if key == 'email':
                UPDATE_SET.update({key : value})

        update_company_phonebook = CompanyPhonebook.objects.filter(id = id).update(**UPDATE_SET)

        return JsonResponse({'message' : '새로운 연락처가 등록되었습니다.'}, status = 200)

class InquireCompanyPhonebookView(View):
    def get(self, request):
        company_id = request.GET.get('company_id')

        check = list(CompanyPhonebook.objects.filter(company_id = company_id).values(
            'id',
            'name',
            'mobile',
            'email'
        ))

        return JsonResponse({'message' : check}, status = 200)

class DeleteCompanyPhonebookView(View):
    def post(self, request):
        company_phonebook_id = request.POST['id']

        CompanyPhonebook.objects.filter(id = company_phonebook_id).delete()

        return JsonResponse({'message' : '삭제성공'}, status = 200)

class CompanyModifyView(View):
    @jwt_decoder
    def post(self, request):
        modify_data = request.POST
        company_id = request.GET.get('id')
        company = Company.objects.filter(id = company_id)

        REGEX_CODE = '[A-Z]{2}'

        if company.exists() == False:
            return JsonResponse({'message' : "존재하지 않는 회사입니다."}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name','keyword','represent','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

                for key, value in modify_data.items():
                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    if key == 'code':
                        if not re.fullmatch(REGEX_CODE, value):
                            return JsonResponse({'message' : '회사 코드 형식을 확인해주세요. [A-Z] 2자리'}, status = 403)

                        if Company.objects.filter(code = modify_data['code']).exists():
                            return JsonResponse({'message' : '회사 코드가 이미 존재합니다.'}, status = 403)
                        UPDATE_SET.update({ key : value })
                    
                Company.objects.filter(id = company_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)


class CompnayStatusView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        user = request.user
        company_id = input_data.get('company_id', None)
        try:
            with transaction.atomic():

                if not company_id:
                    return JsonResponse({'message' : "company_id를 입력해주세요"}, status = 403)

                if user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)

                if input_data['status'] == "False":
                    Company.objects.filter(id = company_id).update( status = False)
                    return JsonResponse({'message' : '회사 상태 False'}, status = 200)
                
                if input_data['status'] == "True": 
                    Company.objects.filter(id = company_id).update( status = True)
                    return JsonResponse({'message' : '회사 그룹 상태 True'}, status = 200)

        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'}, status = 403)

# -------------------------------------------------------------------------------------------------------------#

class CustomTitleListView(View):
    def get(self, request):
        Title_list = list(CustomTitle.objects.filter().values())
        
        
        return JsonResponse({'message' : Title_list}, status = 200)
        
class CustomTitleCreateView(View):
    def post(self, request):
        title   = request.POST['title']

        try:
            new_custom_title = CustomTitle.objects.create(
                title = title,
                status = True
            )
        
            return JsonResponse({'message' : 'cusutom title 생성 성공'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '잘못된 key 값을 입력하셨습니다.'}, status = 403)

class CustomTitleModifyView(View):
    def post(self, request):
        id      = request.POST['custom_title_id']
        
        UPDATE_SET = {}

        for key, value in request.POST.items():
            if key == 'title':
                UPDATE_SET.update({key : value})
            
            if key == 'status':
                if value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                UPDATE_SET.update({key : value})
    
        try:
            CustomTitle.objects.filter(id = id).update(**UPDATE_SET)
            
            return JsonResponse({'message' : '커스텀 타이틀 수정을 성공했습니다.'}, status = 200)
        except CustomTitle.DoesNotExist:
            return JsonResponse({'message' : f'title id를 확인해주세요. {id}'}, status = 403)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)  

class CustomValueListView(View):
    def get(self, request):
        company_id = request.GET.get('company_id')

        Use_Titles = CustomTitle.objects.filter(status = True).values_list('id', flat= True)
        
        result = []
        for title_id in Use_Titles:
            try:
                value = CustomValue.objects.get(company_id = company_id, custom_title_id = title_id).value
                dict = {}
                dict.update({
                    'title_id' : title_id,
                    'contents' : value        
                    })
                result.append(dict)
            except CustomValue.DoesNotExist:
                pass

        return JsonResponse({'message' : result}, status = 200)

class CustomValueCreateView(View):
    def post(self, request):
        custom_title_id = request.POST['title_id']
        company_id      = request.POST['company_id']
        value           = request.POST['value']

        try:
            obj, check = CustomValue.objects.update_or_create(
                custom_title_id = custom_title_id,
                company_id = company_id,
                defaults={ 'value' : value}
                )
            if check == True:
                return JsonResponse({'message' : 'cusutom value 생성 성공'}, status = 200)
            else:
                return JsonResponse({'message' : 'cusutom value 수정 성공'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '잘못된 key 값을 입력하셨습니다.'}, status = 200)