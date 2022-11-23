import json

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection
from django.db.models   import Q


# Model
from users.models       import *
from products.models    import *
from companies.models   import *
from locations.models   import *

# decorator & utills 
from users.decorator    import jwt_decoder, check_status
from products.utils     import *

class ProductGroupView(View):
    def get(self, request):
        name = request.GET.get('name')
        code = request.GET.get('code')
        
        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if code:
                q &= Q(code__icontains = code)
            
            result = list(ProductGroup.objects.filter(q).values())
        
            return JsonResponse({'message' : result}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
   
    def post(self, request):
        input_data = request.POST

        
        if not "name" in input_data:
            return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

        if ProductGroup.objects.filter(name = input_data['name']).exists():
                return JsonResponse({'message' : 'The product name is already registered.'}, status = 403)

        if ProductGroup.objects.filter(code = input_data['code']).exists():
                return JsonResponse({'message' : 'The product code is already registered.'}, status = 403)     
            
        CREATE_SET = {}
        CREATE_OPT = ['name', 'code', 'etc']
        # create_options 로 request.POST 의 키값이 정확한지 확인.
        for key in dict(request.POST).keys():
            if key in CREATE_OPT:
                CREATE_SET.update({ key : request.POST[key] })
            else:
                return JsonResponse({'message' : '잘못된 키값이 들어오고 있습니다.'}, status = 403)

        new_product_group = ProductGroup.objects.create(**CREATE_SET)

        check_PG = list(ProductGroup.objects.filter(id = new_product_group.id).values(
            'id',
            'name',
            'code',
            'etc',
            'status'
        ))

        return JsonResponse({'message' : check_PG}, status = 200)

class ModifyProductGroupView(View):
    def post(self, request):
        input_data = request.POST
        group_id = request.GET.get('group_id')

        if not ProductGroup.objects.filter(id = group_id).exists():
            return JsonResponse({'message' : '존재하지 않는 제품그룹입니다.'}, status = 403)

        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name', 'etc']

                for key, value in input_data.items():
                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    
                ProductGroup.objects.filter(id = group_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class ProductD1InfoView(View):
    def get(self, request):
        company_code = request.GET.get('company_code', None)
        keyword = request.GET.get('keyword', None)
        name = request.GET.get('name', None)
        productgroup_code = request.GET.get('productgroup_code', None)

        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if company_code:
                q &= Q(company_code__icontains = company_code)
            if keyword:
                q &= Q(search_word__icontains = keyword)
            if productgroup_code:
                q &= Q(productgroup_code__icontains = productgroup_code)
            
            result = list(ProductD1.objects.filter(q).values())
        
            return JsonResponse({'message' : result}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
    
    def post(self, request):
        input_data = request.POST

        if not 'name' in input_data:
            return JsonResponse({'message' : '제품명을 입력해주세요'}, status = 403)

        if not 'productgroup_code' in input_data:
            return JsonResponse({'message' : '제품 코드를 입력해주세요'}, status = 403)

        if not ProductGroup.objects.filter(code = input_data['productgroup_code']).exists():
            return JsonResponse({'message' : '존재하지 않는 제품그룹 코드입니다.'}, status = 403)
        
        if 'warehouse_code' in input_data:
            if not Warehouse.objects.filter(code = input_data['warehouse_code']).exists():
                return JsonResponse({'message' : '존재하지 않는 창고 코드입니다.'}, status = 403)
        
        with transaction.atomic():
            if 'company_code' in input_data:
                
                if not Company.objects.filter(code = input_data['company_code']).exists():
                    return JsonResponse({'message' : '존재하지 않는 회사 코드입니다.'})
                
                product_d1 = ProductD1.objects.filter(productgroup_code = input_data['productgroup_code']) 

                if product_d1.exists():
                    productgroup_num = product_d1.latest('created_at').product_num
                    change_int_num = int(productgroup_num) + 1
                    input_num = str(change_int_num).zfill(3)           
                else:
                    input_num = '001'
                
                CREATE_SET = {
                    'productgroup_code' : input_data['productgroup_code'],
                    'product_num' : input_num,
                    'company_code' : input_data['company_code']
                }
                for key, value in input_data.items():
                    if key in ['safe_quantity', 'keyword', 'warehouse_code', 'location']:
                        CREATE_SET.update({key : value})
                
                ProductD1.objects.create(**CREATE_SET)
                return JsonResponse({'message' : '새로운 제품 등록'}, status = 200)
            
            else:
                product_d1 = ProductD1.objects.filter(productgroup_code = input_data['productgroup_code']) 

                if product_d1.exists():
                    productgroup_num = product_d1.latest('created_at').product_num
                    change_int_num = int(productgroup_num) + 1
                    input_num = str(change_int_num).zfill(3)           
                else:
                    input_num = '001'
                
                CREATE_SET = {
                    'productgroup_code' : input_data['productgroup_code'],
                    'name' : input_data['name'],
                    'product_num' : input_num
                }
                for key, value in input_data.items():
                    if key in ['safe_quantity', 'keyword', 'warehouse_code', 'location']:
                        CREATE_SET.update({key : value})
                
                ProductD1.objects.create(**CREATE_SET)
                return JsonResponse({'message' : '새로운 제품 등록'}, status = 200)
        

class ProductD1CompanyView(View):
    def get(self, request):
        productD1_id = request.GET.get('productD1_id')

        D1_company_list = list(ProductD1Company.objects.filter(productD1_id = productD1_id).values())    
    
        return JsonResponse({'message' : D1_company_list}, status = 200)

    def post(self, request):
        input_data = request.POST

        if not ProductD1.objects.filter(id = input_data['productD1_id']).exists():
            return JsonResponse({'message' : '존재하지 않는 제품(D1) id입니다.'}, statue = 403)

        if not Company.objects.filter(code = input_data['company_code']).exists():
            return JsonResponse({'message' : '존재하지 않는 회사 코드 입니다.'}, statue = 403)
        try:
            with transaction.atomic():
                ProductD1Company.objects.create(
                    productD1_id = input_data['productD1_id'], 
                    company_code = input_data['company_code'])
            return JsonResponse({'message' : '제품(D1)에 회사가 등록되었습니다.'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항이 발생했습니다.'}, status = 403)

    def delete(self, request):
        id = request.GET.get('id')
        
        if not ProductD1Company.objects.filter(id = id).exists():
            return JsonResponse({'message' : '존재하지 않는 id 입니다.'}, statue = 403)

        ProductD1Company.objects.delete(id = id)

        return JsonResponse({'message' : f'id({id})삭제 했습니다.'}, status = 200)

class ModifyProductD1InfoView(View):
    def post(self, request):
        modify_data = request.POST
        
        if ProductD1.objects.filter(id = modify_data['id']).exists() == False:
            return JsonResponse({'message' : "존재하지 않는 제품입니다."}, status = 403)
        
        UPDATE_SET = {}
        UPDATE_OPT = ['quantity', 'safe_quantity', 'keyword', 'name']

        try:
            with transaction.atomic():

                for key, value in modify_data.items():
                    if key in UPDATE_OPT:
                        UPDATE_SET.update({key : value})
                
                ProductD1.objects.filter(id = modify_data['id']).update(**UPDATE_SET)

                return JsonResponse({'message' : 'Check update'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

class ProductEtcTitleView(View):
    def post(self, request):
        input_data = request.POST
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                for key, value in input_data.items():
                    if key == 'product_etc_title':
                        UPDATE_SET.update({'title' : value})
                    if key == 'product_etc_status':
                        if value == 'false':
                            UPDATE_SET.update({'status': False})
                        elif value == 'true':
                            UPDATE_SET.update({'status': True})

                ProductEtcTitle.objects.filter(id = input_data['product_etc_id']).update(**UPDATE_SET)
                return JsonResponse({'message' : 'updated'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

    def get(self, request):
        # 권한 설정
        title_list = list(ProductEtcTitle.objects.all().values()) 

        return JsonResponse({'message' : title_list}, status = 200)

class ProductD1EtcDescView(View):
    def post(self, request):
        input_data = request.POST
        
        # 필수 입력 정보 확인
        if not 'productD1_id' in input_data:
            return JsonResponse({'message' : '수정할 제품(D1)가 입력되지 않았습니다'}, status = 403)

        if not 'title_id' in input_data:
            return JsonResponse({'message' : '수정할 제목이 선택되지 않았습니다.'}, status = 403)

        # 거래처 확인
        if not ProductD1.objects.filter(id = input_data['productD1_id']).exists():
            return JsonResponse({'message' : '존재하지 않는 제품(D1)입니다. '}, status = 403)

        try:
            with transaction.atomic():        
                # 이미 등록된 정보가 있는지 확인
                obj , created = ProductD1EtcDesc.objects.update_or_create(productD1_id = input_data['productD1_id'], product_etc_title_id = input_data['title_id'],
                defaults={
                    'productD1_id' : input_data['productD1_id'],
                    'product_etc_title_id' : input_data['title_id'],
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
            'productD1_id' : 'productD1_id__exact',
        }        

        filter_set = { filter_options.get(key) : value for (key, value) in request.GET.items() if filter_options.get(key) }
        
        result = list(CompanyEtcDesc.objects.filter(**filter_set).values())
        
        return JsonResponse({'message' : result}, status = 200)
###########################################################################################################

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

