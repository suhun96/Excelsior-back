import json

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection
from django.db.models   import Q


# Model
from users.models       import *
from products.models    import *

# decorator & utills 
from users.decorator    import jwt_decoder, check_status
from products.utils     import *

class ProductGroupView(View):
    def get(self, request):
        name = request.GET.get('name', None)
        code = request.GET.get('code', None)
        sort = request.GET.get('sort', None)
        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if code:
                q &= Q(code__icontains = code)

            order_condition = {
                'up' : 'name',
                'down' : '-name'
            }
            if sort in order_condition:
                sort = (order_condition[sort])

            
            result = list(ProductGroup.objects.filter(q).order_by(sort).values())
        
            return JsonResponse({'message' : result}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
   
    def post(self, request):
        input_data = request.POST

        # try:
        if not "name" in input_data or not "code" in input_data:
            return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

        new_PG , is_created = ProductGroup.objects.filter(
            Q(name = input_data['name']) | Q(code = input_data['code'])
        ).get_or_create(
            defaults= {
                'name' : input_data['name'],
                'code' : input_data['code'],
                'etc'  : input_data['etc']
            })

        if is_created == False:
            return JsonResponse({'messaga' : 'The product code(name) is already registered.'}, status = 403)      

        check_PG = list(ProductGroup.objects.filter(id = new_PG.id).values(
            'id',
            'name',
            'code',
            'etc'
        ))

        return JsonResponse({'message' : check_PG}, status = 200)
        # except KeyError:
        #     return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class CompanyView(View):
    def get(self, request):
        
        filter_options = {
            'name'     : 'name__icontains',
            'keyword'  : 'keyword__icontains',
            'code'     : 'code__icontains',
            'owner'    : 'ownet__icontains',
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
                if not "name" in input_data or not "code" in input_data or not "phone" in input_data:
                    return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)
            
                create_options = ['name','keyword','code','present','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

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
                    'owner',    
                    'biz_no',   
                    'biz_type', 
                    'biz_item', 
                    'phone',    
                    'fax',         
                    'email',    
                    'address_main', 
                    'address_desc', 
                    'zip_code',  
                ))

            return JsonResponse({'message' : check_created}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

    def put(self, request):
        modify_data = json.loads(request.body)
        company_code = request.GET.get('code')
        company = Company.objects.filter(code = company_code)

        if company.exists() == False:
            return JsonResponse({'message' : "존재하지 않는 회사입니다."}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name','keyword','owner','biz_no','biz_type','biz_item','phone','fax','email','address_main','address_desc','zip_code']

                for key, value in modify_data.items():
                    if not key in update_options:
                        return JsonResponse({'message' : f'{key} 존재하지 않는 키값입니다.'}, status = 403)
                    UPDATE_SET.update({ key : value })
                    
                Company.objects.filter(code = company_code).update(**UPDATE_SET)
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
    
class ProductD1InfoView(View):
    def get(self, request):
        code = request.GET.get('code')
        search_word = request.GET.get('search_word')
        name = request.GET.get('name')

        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if code:
                q &= Q(code__icontains = code)
            if search_word:
                q &= Q(search_word__icontains = search_word)
            
            result = list(ProductD1.objects.filter(q).values(
                'id',
                'code',
                'quantity',
                'safe_quantity',
                'search_word',
                'name'
            ))
        
            return JsonResponse({'message' : result}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
    
    def post(self, request):
        input_data = request.POST
        
        try:
            with transaction.atomic():
                product_D1_code = code_generator_d1(input_data['pg_code'], input_data['cp_code'])

                # 제품 정보
                ProductD1.objects.create(
                    code = product_D1_code,
                    quantity = 0,
                    safe_quantity = input_data['safe_quantity'],
                    search_word = input_data['search_word'],
                    name = input_data['name']
                )
                return JsonResponse({f'{product_D1_code}' : 'Product information has been registered.'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)

    def put(self, request):
        body_data= json.loads(request.body)
        comp_code = request.GET.get('code')
        product_D1 = ProductD1.objects.filter(code = comp_code)

        if product_D1.exists() == False:
            return JsonResponse({'message' : "존재하지 않는 제품입니다."}, status = 403)
        try:
            with transaction.atomic():
                UPDATE_SET = {}
                
                for key, value in body_data.items():
                    UPDATE_SET.update({key : value})
                
                ProductD1.objects.filter(code = comp_code).update(**UPDATE_SET)

                return JsonResponse({'message' : 'Check update'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)
          
class ProductD2InfoView(View):
    def get(self, request):
        code = request.GET.get('code', None)
        search_word = request.GET.get('search_word')
        name = request.GET.get('name')

        try:
            if code == None:
                q = Q()
                if name:
                    q &= Q(name__icontains = name)
                if code:
                    q &= Q(code__icontains = code)
                if search_word:
                    q &= Q(search_word__icontains = search_word)
                
                result = list(ProductD2.objects.filter(q).values(
                'code',
                'quantity',
                'safe_quantity',
                'search_word',
                'name'
                ))
                
                return JsonResponse({'bom_info' : result}, status = 200)
            
            if code == code:
                result = list(ProductD2.objects.filter(code = code).values(
                    'code',
                    'quantity',
                    'safe_quantity',
                    'search_word',
                    'name'
                ))
                d2_comp_codes = ProductD2Composition.objects.filter(d2_code = code).values('com_code', 'com_quan')
                dict = {}
                for code in d2_comp_codes:
                    dict.update({code['com_code'] : code['com_quan']})
            
                return JsonResponse({'Info' : result, 'component' : dict}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)

    def post(self, request):
        input_data = json.loads(request.body)

        try:
            with transaction.atomic():
                d2_code = code_generator_d2(input_data['pg_code'], 'EX')

                # 제품 정보
                ProductD2.objects.create(
                    code = d2_code,
                    quantity = 0,
                    safe_quantity = input_data['safe_quantity'],
                    search_word = input_data['search_word'],
                    name = input_data['name']
                )
                # ProductD2Composition 생성
                for com_code, quantity in input_data['components'].items():
                    if not ProductD1.objects.filter(code = com_code).exists():
                        return JsonResponse({'message' : f'{com_code}는 존재하지 않는 코드입니다.'}, status = 403)
                    
                    ProductD2Composition.objects.create( d2_code = d2_code, com_code = com_code, com_quan = quantity)

            return JsonResponse({f'{d2_code}' : 'Product information has been registered.'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)

    def put(self, request):
        modify_data = json.loads(request.body)
        d2_code = request.GET.get('code')
        d2 = ProductD2.objects.filter(code = d2_code)

        # D2에 등록된 제품인지 확인.
        if d2.exists() == False:
            return JsonResponse({'message' : '존재하지 않는 제품입니다.'}, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}
                
                for key, value in modify_data.items():
                    check_list = ['quantity', 'safe_quantity', 'search_word', 'name']

                    if key in check_list:
                        UPDATE_SET.update({key : value})
                    
                    if key == 'components':
                        for com_code in modify_data['components'].keys():
                            if ProductD1.objects.filter(code = com_code).exists():
                                pass
                            else:
                                return JsonResponse({'message' : f'{ com_code }존재하지 않는다 !'}, status = 403)
                        
                        ProductD2Composition.objects.filter(d2_code = d2_code).delete()
                        
                        for com_code, quantity in modify_data['components'].items():
                            ProductD2Composition.objects.create(d2_code = d2_code, com_code = com_code, com_quan = quantity)
                    
                    else:
                        pass

                ProductD2.objects.filter(code = d2_code).update(**UPDATE_SET)
                return JsonResponse({'message' : 'Check update'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

class ProductD3InfoView(View):
    def get(self, request):
        code = request.GET.get('code', None)
        search_word = request.GET.get('search_word')
        name = request.GET.get('name')

        try:
            if code == None:
                q = Q()
                if name:
                    q &= Q(name__icontains = name)
                if code:
                    q &= Q(code__icontains = code)
                if search_word:
                    q &= Q(search_word__icontains = search_word)
                
                result = list(ProductD3.objects.filter(q).values(
                'code',
                'quantity',
                'safe_quantity',
                'search_word',
                'name'
                ))
                
                return JsonResponse({'set_info' : result}, status = 200)
            
            if code == code:
                result = list(ProductD3.objects.filter(code = code).values(
                    'code',
                    'quantity',
                    'safe_quantity',
                    'search_word',
                    'name'
                ))
                set_comp_codes = ProductD3Composition.objects.filter(d3_code = code).values('com_code', 'com_quan')
                dict = {}
                for code in set_comp_codes:
                    dict.update({code['com_code'] : code['com_quan']})
            
                return JsonResponse({'Info' : result, 'component' : dict}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)

    def post(self, request):
        input_data = json.loads(request.body)

        try:
            with transaction.atomic():
                # D3 코드생성 기준 정해야함.
                d3_code = code_generator_d3('ST', 'EX')

                # 제품 정보
                ProductD3.objects.create(
                    code = d3_code,
                    quantity = 0,
                    safe_quantity = input_data['safe_quantity'],
                    search_word = input_data['search_word'],
                    name = input_data['name']
                )
                # components 제품 코드 확인
                for com_code in input_data['components'].keys():
                    if ProductD1.objects.filter(code = com_code).exists():
                        pass
                    elif ProductD2.objects.filter(code = com_code).exists():
                        pass
                    else:
                        raise KeyError
                
                # ProductD3Composition 생성
                for com_code, quantity in input_data['components'].items():
                    ProductD3Composition.objects.filter(d3_code = d3_code, com_code = com_code, com_quan = quantity)
            
            return JsonResponse({f'{d3_code}' : 'Product information has been registered.'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)
    
    def put(self, request):
        modify_data = json.loads(request.body)
        d3_code = request.GET.get('code')
        d3 = ProductD3.objects.filter(code = d3_code)

        # Product D3가 등록된 제품인지 확인.
        if d3.exists() == False:
            return JsonResponse({'message' : '존재하지 않는 제품입니다.'}, status = 403)
        try:
            with transaction.atomic():
                UPDATE_SET = {}
                
                for key, value in modify_data.items():
                    # 업데이트 키 값 확인.
                    check_list = ['quantity', 'safe_quantity','search_word', 'name']
                    if key in check_list:
                        UPDATE_SET.update({key : value})
                    
                    # 구성품 업데이트.
                    # 빈 값 제거.
                    if key == 'components':
                        if modify_data['components'] == {}:
                            return JsonResponse({'message' : '빈 값을 받았습니다.'}, status = 403)
                        # 구성품이 D1,D2에 등록된 상품인지 체크
                        for com_code in modify_data['components'].keys():
                            if   ProductD1.objects.filter(code = com_code).exists():
                                pass
                            elif ProductD2.objects.filter(code = com_code).exists():
                                pass
                            else:
                                return JsonResponse({'message' : '존재하지 않는다 !'}, status = 403)
                        # 체크 후 이 전에 등록 되었던 구성품 전부 삭제.
                        ProductD3Composition.objects.filter(d3_code = d3_code).delete()
                        # 새로운 구성품 등록.
                        for com_code, quantity in modify_data['components'].items():
                            ProductD3Composition.objects.create(d3_code = d3_code, com_code = com_code, com_quan = quantity)

                ProductD3.objects.filter(code = d3_code).update(**UPDATE_SET)
                return JsonResponse({'message' : 'Check update'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)



























# class CreateInboundOrderView(View):
#     @jwt_decoder
#     @check_status
#     def post(self, request):
#         body_data= json.loads(request.body)
#         user = request.user
        
#         try:
#             with transaction.atomic():
#                 # 회사 코드 확인
#                 if not 'company_code' in body_data:
#                     return JsonResponse({'message': "Company code does not exist."}, status = 403)
#                 company_code = body_data['company_code']
#                 # 기타사항 입력 과 미입력 값 조정
#                 if 'etc' in body_data:
#                     etc = body_data['etc']
#                 else:
#                     etc = ''    

#                 # 새로운 입고확인서 생성
#                 new_order = InboundOrder.objects.create(
#                     user_id = user.id,
#                     company_code =  body_data['company_code'],
#                     etc = etc
#                 ) 

#                 new_order_id = new_order.id

                
#                 for product_code in body_data.keys():
#                     # 입력값 필터링
#                     if str(product_code[0:4]).isupper() == True:
#                         product_code = product_code # 시리얼 코드안에 있는 가격, 수량 정보 가져옴
#                         print(product_code)
#                         price = body_data[product_code]['price']
#                         quantity = body_data[product_code]['Q']
#                         # 제품 정보 테이블에서 시리얼 코드가 있는지 확인
#                         if not ProductInfo.objects.filter(product_code__contains = product_code).exists():
#                             raise Exception(f'{product_code} 가 존재하지 않습니다')
#                         # 입고확인서 ID를 입력하여 입고된 상품의 정보 테이블에 저장
#                         InboundQuantity.objects.create(
#                             inbound_order_id = new_order_id,
#                             product_code = product_code,
#                             inbound_price = price,
#                             inbound_quntity = quantity
#                         )
#                         # 입고된 내용을 통해 제품 history, 제품 회사 - 가격 테이블 생성 (바코드 생성 및 저장)
#                         product_history_generator(product_code, quantity, price, etc)
#                         update_product_his(product_code) # 기존에 있는 수량과 입고된 수량 파악 후 저장.
#                         update_price(product_code, price, company_code)
                        

#             return JsonResponse({'message' : 'Inbounding processing has been completed.'}, status = 200)
#         except KeyError:
#             return JsonResponse({'message' : 'Key error'}, status = 403)
#         except Exception as e:
#             return JsonResponse({'message' : 'An exception occurred while running.'}, status = 403)

# class CreateOutboundOrderView(View):
#     @jwt_decoder
#     @check_status
#     def post(self, request):
#         input_data = json.loads(request.body) # 여기서는 request.body를 사용
#         user = request.user
#         try:
#             with transaction.atomic():
#                 #input_data 에서 받은 값에 company_code가 들어있는지 체크
#                 if not 'company_code' in input_data:
#                     return JsonResponse({'message': "Company code does not exist."}, status = 403)
                
#                 #input_data 에서 받은 값으로 새로운 출고 주문서 생성
#                 new_OB_order = OutboundOrder.objects.create(
#                     user_id = user.id,
#                     company_code = input_data['company_code'],
#                     etc = input_data['etc']
#                 )
    
#                 new_OB_order_id = new_OB_order.id

                
#                 for product_code in input_data.keys():
#                     # 길이가 7인 값 = 시리얼 코드
#                     if len(product_code) == 7:
#                         product_code = product_code
#                         price = input_data[product_code]['price']
#                         quantity = input_data[product_code]['Q']

#                         # 제품 정보 테이블에서 시리얼 코드를 검색 없으면 예외를 일으켜 트랜젝션 작동
#                         if not ProductInfo.objects.filter(product_code__icontains = product_code).exists():
#                             raise Exception(f'{product_code} 가 존재하지 않습니다')
#                         # 제품이 있으면 수량, 가격, 생성한 출고 id로 OutboundQunatity 테이블 생성 
#                         OutboundQuantity.objects.create(
#                             outbound_order_id = new_OB_order_id,
#                             product_code = product_code,
#                             outbound_price = price,
#                             outbound_quantity = quantity
#                         )

#                 # ConfirmOutboundOrderView 에서 사용할 딕셔너리 생성
#                 Confirm_query = OutboundQuantity.objects.filter(outbound_order = new_OB_order_id).values('product_code', 'outbound_quantity')
#                 check_product_code = {}

#                 for query in Confirm_query:
#                     product_code = query['product_code']
#                     quantity    = query['outbound_quantity']
#                     check_product_code[product_code] = int(quantity)

                
#             return JsonResponse({"product_codes" : check_product_code }, status = 200)
#         except KeyError:
#             return JsonResponse({'message' : 'Key error'}, status = 403)
#         except Exception as e:
#             return JsonResponse({'message' : 'An exception occurred while running.'}, status = 403)

# class ConfirmOutboundOrderView(View):
#     @jwt_decoder
#     @check_status
#     def post(self, request):
#         input_data = json.loads(request.body)
#         try:
#             with transaction.atomic():
#                 OB_id = input_data['OB_id']
#                 company_code = OutboundOrder.objects.get(id = OB_id).company_code

#                 # {프로덕트 코드 : 바코드 수량} 비교 딕셔너리 생성.
#                 product_codes_dic = {}
#                 check_status = OutboundQuantity.objects.filter(outbound_order_id = OB_id).values('product_code', 'outbound_quantity')
#                 for i in range(len(check_status)):
#                     product_codes_dic[check_status[i]['product_code']] = check_status[i]['outbound_quantity']

#                 barcodes = input_data['barcodes']
                
#                 # 바코드를 슬라이싱해 프로덕트 코드화 딕셔너리 key 값에 슬라이싱한 바코드를 넣어 {프로덕트 코드 : 바코드 수량} 딕셔너리 값을 하나 차감.
#                 for i in range(len(barcodes)):
#                     slicing_product_code = barcodes[i][:7]

#                     if not slicing_product_code in product_codes_dic.keys():
#                         return JsonResponse({'message' : 'Please check the first 7 digits of the product code.'}, status = 403 )
#                     product_codes_dic[slicing_product_code] = int(product_codes_dic[slicing_product_code]) - 1
                
#                 # {프로덕트 코드 : 바코드 수량} 바코드 수량이 0이 되지않으면 (즉, 같은 딕셔너리에 포함된 같은 프로덕트 코드 값의 바코드가 들어오지 않았음) return 값 작동.
#                 for i in product_codes_dic.values():
#                     if not i == 0:
#                         return JsonResponse({"product_codes" : 'The barcode entered and the outbounding order do not match.' }, status = 200)
                
#                 for barcode in barcodes:
#                     # 바코드 검증 use_status가 1이 아니면 return 값 작동.
#                     if not ProductHis.objects.get(barcode = barcode).use_status == 1 :
#                         return JsonResponse({'message' : 'Barcode already used.'}, status = 403 )
#                     product_code = barcodes[i][:7]
                    
#                     # 사용한 바코드 use_status 변경(사용함 = 2) 
#                     # OutboundBarcode Table에 OB 아이디와 바코드 저장 부품 추적시 사용.
#                     ProductHis.objects.filter(barcode = barcode).update(use_status = 2)
#                     OutboundBarcode.objects.create(outbound_order_id = OB_id, barcode = barcode)
#                     update_product_his(product_code)
                    
#                      # 제품 정보에 수량 수정사항(사용 가능한 수량, 회사 - 출고 가격) 반영.
#                     outbound_price = OutboundQuantity.objects.get(product_code = product_code, outbound_order_id = OB_id).outbound_price
#                     update_product_his(product_code)
#                     update_price(product_code, outbound_price, company_code)
                    
#             return JsonResponse({"product_codes" : 'processing completed.' }, status = 200)
#         except KeyError:
#             return JsonResponse({'message' : 'Key error'}, status = 403)

# class CreateSetInfoView(View):
#     def __init__(self):
#         # 날짜 설정
#         now = datetime.now()
#         self.year    = str(now.year)
#         self.month   = str(now.month)
#         self.day     = str(now.day) 

#     def serial_generator(self, pg_code):
#         product_group  = ProductGroup.objects.filter(code = pg_code)
        
#         # 제품 그룹이 있는지 체크
#         if product_group.exists() == False:
#             raise ValueError('Product group that does not exist.')

#         CPPG = 'EX' + pg_code # SSPP 
#         # 형번을 생성 등록된 제품 정보를 참고해 CPPG 가 존재하면 그 다음 형번을 부여 없으면 1로 시작.
#         if SetProductInfo.objects.filter(set_product_code__icontains = CPPG).exists():
#             latest_product_code = SetProductInfo.objects.filter(set_product_code__icontains = CPPG).latest('created_at').set_product_code
#             model_number = int(latest_product_code[5:7]) + 1
#         else:
#             model_number = 1

#         model_number = str(model_number).zfill(3)
#         # 제품 시리얼 코드 생성 SSPP001
#         set_product_code = CPPG + model_number
        
#         return set_product_code


#     def post(self, request):
#         input_data = json.loads(request.body)
#         set_product_code = self.serial_generator(input_data['pgcode'])
        
#         try:
#             with transaction.atomic():
#                 new_set = SetProductInfo.objects.create(
#                     set_product_code = set_product_code,
#                     quantity = input_data['quantity'],
#                     safe_quantity = input_data['safe_quantity'],
#                     search_word = input_data['search_word'],
#                     name = input_data['name']
#                     )
                
#                 product_codes = input_data['product_code']
#                 for product_code in product_codes:
#                     quantity = int(product_codes[product_code])
#                     if not ProductInfo.objects.filter(product_code__icontains = product_code).exists():
#                         raise Exception(f'{product_code} 가 존재하지 않습니다')
                    
#                     SetProductQuantity.objects.create(
#                         set_product_code = set_product_code,
#                         product_code = product_code,
#                         product_quantity = quantity
#                     )
                
#                 set_product_history_generator(set_product_code, input_data['quantity'],input_data['price'] ,input_data['etc'] )

#             return JsonResponse({'mesaage' : 'Product information has been registered.'}, status = 200) 
#         except KeyError:
#             return JsonResponse({'mesaage' : 'Key Error'}, status = 403) 

# class PrintProductBarcodeView(View):
#     def __init__(self):
#         now = datetime.now()
#         year    = str(now.year)
#         month   = str(now.month).zfill(2)
#         day     = str(now.day).zfill(2)
#         self.today = year[2:4] + month + day

#     def post(self, request):
#         input_data = request.POST
#         product_code = input_data['product_code']
#         yymmdd = self.today
    
#         try:
#             product_info = ProductInfo.objects.filter(product_code = product_code)
#             print(len(connection.queries))
#             if not product_info.exists():
#                 return JsonResponse({'mesaage' : '존재하지 않는 프로덕트 코드 입니다.'}, status = 403) 

#             if "yymmdd" in input_data:
#                 yymmdd = input_data['yymmdd']
            
#             barcodes = list(print_barcode(product_code, yymmdd))
#             print(len(connection.queries))
#             return JsonResponse({'barcodes' : barcodes }, status = 200) 
#         except KeyError:
#             return JsonResponse({'mesaage' : 'Key Error'}, status = 403) 

# class CheckView(View):
#     def post(self, request):
#         data = request.POST
#         product_code = "SHVV008"
#         yymmdd = '221101'
#         barcodes = list(print_barcode(product_code, yymmdd))
        
#         return JsonResponse({'message' : barcodes}, status = 200)

