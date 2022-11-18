import json

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection
from django.db.models   import Q


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
                    if key in create_options:
                        CREATE_SET.update({ key : request.POST[key] })
                    else:
                        return JsonResponse({'message' : '잘못된 키값이 들어오고 있습니다.'}, status = 403)
        
                # 중복 생성 방지.
                new_company , is_created = Company.objects.filter(
                    Q(name = input_data['name']) | Q(code = input_data['code'])
                ).get_or_create(
                    defaults = {**CREATE_SET} )
                
                if is_created == False:
                    return JsonResponse({'messaga' : 'The company code(name) is already registered.'}, status = 403)      

                check_created = list(Company.objects.filter(id = new_company.id).values(
                    'name',     
                    'keyword',  
                    'code',     
                    'represent',    
                    'biz_no',   
                    'biz_type', 
                    'biz_item', 
                    'phone',    
                    'fax',         
                    'email',    
                    'address_main', 
                    'address_desc', 
                    'zip_code',
                    'status'  
                ))

            return JsonResponse({'message' : check_created}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

    def put(self, request):
        modify_data = json.loads(request.body)
        company_id = request.GET.get('company_id')
        company = Company.objects.filter(id = company_id)

        if company.exists() == False:
            return JsonResponse({'message' : "존재하지 않는 회사입니다."}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name','keyword','represent','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

                for key, value in modify_data.items():
                    if not key in update_options:
                        return JsonResponse({'message' : f'{key} 존재하지 않는 키값입니다.'}, status = 403)
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
        
        # 회사 코드 확인
        if not Company.objects.filter(code = input_data['comp_code']).exists():
            return JsonResponse({'message' : '존재하지 않는 회사 코드입니다.'}, status = 403)
        
        CompanyEtcDesc.objects.create(comp_code = input_data['comp_code'], company_etc_title_id = input_data['title_id'], contents = input_data['contents'])

        return JsonResponse({'message' : 'ok'}, status = 200)

    def get(self, request):

        filter_options = {
            'comp_code' : 'comp_code__icontains'
        }        

        filter_set = { filter_options.get(key) : value for (key, value) in request.GET.items() if filter_options.get(key) }
        
        result = list(CompanyEtcDesc.objects.filter(**filter_set).values())
        
        return JsonResponse({'message' : result}, status = 200)

    def put(self, request):
        comp_code = request.GET.get('comp_code')
        company_etc_title_id = request.GET.get('company_etc_id')
        modify_data = json.loads(request.body)
        
        if not 'comp_code' in request.GET:
            return JsonResponse({'message' : '수정할 회사 코드가 입력되지 않았습니다'}, status = 403)

        if not 'company_etc_id' in request.GET:
            return JsonResponse({'message' : '수정할 제목이 선택되지 않았습니다.'}, status = 403)

        try:
            with transaction.atomic():
                CompanyEtcDesc.objects.filter(comp_code = comp_code, company_etc_title_id = company_etc_title_id).update(
                    contents = modify_data['contents']
                )
            return JsonResponse({'message' : '수정 완료'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

class CompanyPhonebookView(View):
    def get(self, request):
        company_code = request.GET.get('code')

        check = list(CompanyPhonebook.objects.filter(comp_code = company_code).values(
            'id',
            'name',
            'mobile',
            'email'
        ))

        return JsonResponse({'message' : check}, status = 200)
    
    def post(self, request):
        input_data = request.POST

        if Company.objects.filter(code = input_data['code']).exists() == False:
            return JsonResponse({'message' : '존재하지 않는 회사 코드입니다. 코드를 확인해주세요'}, status = 403)
        
        if CompanyPhonebook.objects.filter(comp_code = input_data['code']).count() == 5:
            return JsonResponse({'message' : '등록 가능한 추가 전화번호부를 전부 사용중 입니다.'}, status = 403)

        CompanyPhonebook.objects.create(
            comp_code = input_data['code'],
            name = input_data['name'],
            mobile = input_data['mobile'],
            email = input_data['email']
            )

        return JsonResponse({'test' : 'check'}, status = 200)
    
    def put(self, request):
        company_code = request.GET.get('code')
        company_phonebook_id = request.GET.get('id')
        modify_data = json.loads(request.body)

        if Company.objects.filter(code = company_code).exists() == False:
            return JsonResponse({'message' : '존재하지 않는 회사 코드입니다. 코드를 확인해주세요.'}, status = 403)
        
        if CompanyPhonebook.objects.filter(id = company_phonebook_id, comp_code = company_code).exists() == False:
            return JsonResponse({'message' : '존재하지 않는 정보를 수정할 수 없습니다.'}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name', 'mobile', 'email']

                for key, value in modify_data.items():
                    if not key in update_options:
                        return JsonResponse({'message' : f'{key} 존재하지 않는 키 값입니다.'}, status = 403)
                    UPDATE_SET.update({ key : value})

                CompanyPhonebook.objects.filter(id = company_phonebook_id, comp_code = company_code).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)    
        except:   
            return JsonResponse({'message' : '예외 사항이 발생, 로직을 정지합니다. 삐빅'}, status = 403)