import json

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
from users.decorator    import jwt_decoder, check_status
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

    def post(self, request):
        input_data = request.POST
        
        try:
            with transaction.atomic():
                # 필수값 (이름, 코드, 번호)이 있는지 확인 없으면 에러 발생.
                if not "name" in input_data:
                    return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)
                
                create_options = ['name','keyword','code','represent','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

                CREATE_SET = {}

                # create_options 로 request.POST 의 키값이 정확한지 확인.
                for key in dict(request.POST).keys():
                    if key == 'name':
                        if Company.objects.filter(name = request.POST[key]) == True:
                            return JsonResponse({'message' : '회사 이름이 존재합니다.'}, status = 403)
                        
                        CREATE_SET.update({ key : request.POST[key] }) 
                    
                    if key == 'code':
                        if Company.objects.filter(code = input_data['code']).exists():
                            return JsonResponse({'message' : '회사 코드가 이미 존재합니다.'}, status = 403)
                        
                        CREATE_SET.update({ key : request.POST[key] }) 

                    elif key in create_options:
                        
                        CREATE_SET.update({ key : request.POST[key] })
                    else:
                        return JsonResponse({'message' : '잘못된 키값이 들어오고 있습니다.'}, status = 403)
        
                
                new_company = Company.objects.create(**CREATE_SET)
                # 전화번호부 5개 생성
                for i in range(1,6):
                    CompanyPhonebook.objects.create(company_id = new_company.id)

                check_created = list(Company.objects.filter(id = new_company.id).values())

            return JsonResponse({'message' : check_created}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class CompanyModifyView(View):
    def post(self, request):
        modify_data = request.POST
        company_id = request.GET.get('id')
        company = Company.objects.filter(id = company_id)

        if company.exists() == False:
            return JsonResponse({'message' : "존재하지 않는 회사입니다."}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name','keyword','represent','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code','code']

                for key, value in modify_data.items():
                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    
                Company.objects.filter(id = company_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class CompanyEtcTitleView(View):
    def post(self, request):
        input_data = request.POST
        
        # 나중에 권한 적용
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                for key, value in input_data.items():
                    if key == 'company_etc_title':
                        UPDATE_SET.update({'title' : value})
                    if key == 'company_etc_status':
                        if value == 'false':
                            UPDATE_SET.update({'status': False})
                        elif value == 'true':
                            UPDATE_SET.update({'status': True})

                CompanyEtcTitle.objects.filter(id = input_data['company_etc_id']).update(**UPDATE_SET)
                return JsonResponse({'message' : 'updated'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

    def get(self, request):
        # 권한 설정
        title_list = list(CompanyEtcTitle.objects.all().values('id','title','status')) 

        return JsonResponse({'message' : title_list}, status = 200)   

class CompanyEtcDescView(View):
    def post(self, request):
        input_data = request.POST
        
        # 필수 입력 정보 확인
        if not 'company_id' in input_data:
            return JsonResponse({'message' : '수정할 회사가 입력되지 않았습니다'}, status = 403)

        if not 'title_id' in input_data:
            return JsonResponse({'message' : '수정할 제목이 선택되지 않았습니다.'}, status = 403)

        # 거래처 확인
        if not Company.objects.filter(id = input_data['company_id']).exists():
            return JsonResponse({'message' : '존재하지 않는 회사입니다.'}, status = 403)

        try:
            with transaction.atomic():        
                # 이미 등록된 정보가 있는지 확인
                obj , created = CompanyEtcDesc.objects.update_or_create(company_id = input_data['company_id'], company_etc_title_id = input_data['title_id'],
                defaults={
                    'company_id' : input_data['company_id'],
                    'company_etc_title_id' : input_data['title_id'],
                    'contents' : input_data['contents']
                })
                
            if created == False:
                return JsonResponse({'message' : '기존의 비고란 내용을 수정 했습니다.'}, status = 200)
            else:
                return JsonResponse({'message' : '새로운 비고란 내용을 생성 했습니다.'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항이 발생했습니다.'}, status = 200)
    
    def get(self, request):

        filter_options = {
            'company_id' : 'company_id__exact',
            'company_code' : 'comp_code__icontains'
        }        

        filter_set = { filter_options.get(key) : value for (key, value) in request.GET.items() if filter_options.get(key) }
        
        result = list(CompanyEtcDesc.objects.filter(**filter_set).values())
        
        return JsonResponse({'message' : result}, status = 200)


class CompanyPhonebookView(View):
    def get(self, request):
        company_id = request.GET.get('company_id')

        check = list(CompanyPhonebook.objects.filter(company_id = company_id).values(
            'id',
            'name',
            'mobile',
            'email'
        ))

        return JsonResponse({'message' : check}, status = 200)
    
    def post(self, request):
        input_data = request.POST

        if Company.objects.filter(id = input_data['company_id']).exists() == False:
            return JsonResponse({'message' : '존재하지 않는 회사입니다. 확인해주세요'}, status = 403)

        CompanyPhonebook.objects.filter(id = input_data['id'], company_id = input_data['company_id']).update(
            name = input_data['name'],
            mobile = input_data['mobile'],
            email = input_data['email']
        )

        return JsonResponse({'test' : 'check'}, status = 200)