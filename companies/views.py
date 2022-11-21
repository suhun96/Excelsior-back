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

                check_created = list(Company.objects.filter(id = new_company.id).values())

            return JsonResponse({'message' : check_created}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

    def put(self, request):
        modify_data = json.loads(request.body)
        company_id = request.GET.get('id')
        company = Company.objects.filter(id = company_id)

        if company.exists() == False:
            return JsonResponse({'message' : "존재하지 않는 회사입니다."}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {'updated_at' : datetime.today()}

                update_options = ['name','keyword','represent','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

                for key, value in modify_data.items():
                    if key == 'id':
                        pass
                    elif not key in update_options:
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
        if not Company.objects.filter(id = input_data['company_id']).exists():
            return JsonResponse({'message' : '존재하지 않는 회사입니다.'}, status = 403)

        # 이미 등록된 정보가 있는지 확인
        if CompanyEtcDesc.objects.filter(company_id = input_data['company_id'], company_etc_title_id = input_data['title_id']).exists():
            return JsonResponse({'message' : '등록된 정보가 있습니다. 수정하시겠습니까?'}, status = 403)
        
        CompanyEtcDesc.objects.create(company_id = input_data['company_id'], company_etc_title_id = input_data['title_id'], contents = input_data['contents'])

        return JsonResponse({'message' : 'ok'}, status = 200)

    def get(self, request):

        filter_options = {
            'company_id' : 'id__excact',
            'company_code' : 'comp_code__icontains'
        }        

        filter_set = { filter_options.get(key) : value for (key, value) in request.GET.items() if filter_options.get(key) }
        
        result = list(CompanyEtcDesc.objects.filter(**filter_set).values())
        
        return JsonResponse({'message' : result}, status = 200)

    def put(self, request):
        company_id = request.GET.get('company_id')
        company_etc_title_id = request.GET.get('title_id')
        modify_data = json.loads(request.body)
        
        if not 'company_id' in request.GET:
            return JsonResponse({'message' : '수정할 회사가 입력되지 않았습니다'}, status = 403)

        if not 'company_etc_id' in request.GET:
            return JsonResponse({'message' : '수정할 제목이 선택되지 않았습니다.'}, status = 403)

        try:
            with transaction.atomic():
                CompanyEtcDesc.objects.filter(company_id = company_id, company_etc_title_id = company_etc_title_id).update(
                    contents = modify_data['contents']
                )
            return JsonResponse({'message' : '수정 완료'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

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
        
        if CompanyPhonebook.objects.filter(company_id = input_data['company_id']).count() == 5:
            return JsonResponse({'message' : '등록 가능한 추가 전화번호부를 전부 사용중 입니다.'}, status = 403)

        CompanyPhonebook.objects.create(
            company_id = input_data['company_id'],
            name = input_data['name'],
            mobile = input_data['mobile'],
            email = input_data['email']
            )

        return JsonResponse({'test' : 'check'}, status = 200)
    
    def put(self, request):
        company_id = request.GET.get('company_id')
        company_phonebook_id = request.GET.get('id')
        modify_data = json.loads(request.body)

        if Company.objects.filter(id = company_id).exists() == False:
            return JsonResponse({'message' : '존재하지 않는 회사 코드입니다. 코드를 확인해주세요.'}, status = 403)
        
        if CompanyPhonebook.objects.filter(id = company_phonebook_id, company_id = company_id).exists() == False:
            return JsonResponse({'message' : '존재하지 않는 정보를 수정할 수 없습니다.'}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name', 'mobile', 'email']

                for key, value in modify_data.items():
                    if key == 'id':
                        pass
                    elif not key in update_options:
                        return JsonResponse({'message' : f'{key} 존재하지 않는 키 값입니다.'}, status = 403)
                    UPDATE_SET.update({ key : value})

                CompanyPhonebook.objects.filter(id = company_phonebook_id, company_id = company_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)    
        except:   
            return JsonResponse({'message' : '예외 사항이 발생, 로직을 정지합니다. 삐빅'}, status = 403)