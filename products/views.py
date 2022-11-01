import json

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from django.db.models   import Q
from datetime           import datetime

# Model
from users.models       import *
from products.models    import *

# decorator & utills 
from users.decorator    import jwt_decoder, check_status
from products.utils     import product_history_generator, update_product_his, update_price

class CreateProductGroupView(View):
    @jwt_decoder
    @check_status
    def post(self, request):
        input_data = request.POST

        try:
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
       
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class CreateCompanyView(View):
    @jwt_decoder
    @check_status
    def post(self, request):
        input_data = request.POST

        try:
            if not "name" in input_data or not "code" in input_data:
                return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

            new_CP , is_created = Company.objects.filter(
                Q(name = input_data['name']) | Q(code = input_data['code'])
            ).get_or_create(
                defaults= {
                    'name'       : input_data['name'],
                    'code'       : input_data['code'],
                    'address'    : input_data['address'],
                    'managers'   : input_data['managers'],
                    'telephone'  : input_data['telephone'],
                    'mobilephone': input_data['mobilephone'],
                    'manage_tag' : input_data['manage_tag'],
                    'etc'        : input_data['etc']
                })

            if is_created == False:
                return JsonResponse({'messaga' : 'The company code(name) is already registered.'}, status = 403)      

            check_CP = list(Company.objects.filter(id = new_CP.id).values(
                'name',       
                'code',      
                'address',    
                'managers',   
                'telephone',  
                'mobilephone',
                'manage_tag', 
                'etc'        
            ))

            return JsonResponse({'message' : check_CP}, status = 200)
       
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class CreateProductInfoView(View):
    def __init__(self):
        # 날짜 설정
        now = datetime.now()
        self.year    = str(now.year)
        self.month   = str(now.month)
        self.day     = str(now.day) 

    def serial_generator(self, pg_code, cp_code):
        product_group  = ProductGroup.objects.filter(code = pg_code)
        company        = Company.objects.filter(code = cp_code)
        
        # 제품 그룹이 있는지 체크
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')
        # 회사가 등록이 되어있는지
        if company.exists() == False:
            raise ValueError('Company (trade name) that does not exist.')

        CPPG = cp_code + pg_code # SSPP 
        # 형번을 생성 등록된 제품 정보를 참고해 CPPG 가 존재하면 그 다음 형번을 부여 없으면 1로 시작.
        if ProductInfo.objects.filter(product_code__icontains = CPPG).exists():
            latest_product_code = ProductInfo.objects.filter(product_code__icontains = CPPG).latest('created_at').product_code
            model_number = int(latest_product_code[5:7]) + 1
        else:
            model_number = 1

        model_number = str(model_number).zfill(3)
        # 제품 시리얼 코드 생성 SSPP001
        product_code = cp_code + pg_code + model_number
        
        return product_code


    def post(self, request):
        input_data = request.POST

        try:
            product_code = self.serial_generator(input_data['pg_code'], input_data['cp_code'])
            
            print(product_code)

            ProductInfo.objects.create(
                product_code = product_code,
                quantity = input_data['quantity'],
                safe_quantity = input_data['safe_quantity'],
                search_word = input_data['search_word'],
                name = input_data['name']
                )


            product_history_generator(product_code, input_data['quantity'],input_data['price'] ,input_data['etc'] )


            return JsonResponse({'mesaage' : 'Product information has been registered.'}, status = 200) 
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)

class CreateInboundOrderView(View):
    @jwt_decoder
    @check_status
    def post(self, request):
        body_data= json.loads(request.body)
        user = request.user
        
        try:
            with transaction.atomic():
                # 회사 코드 확인
                if not 'company_code' in body_data:
                    return JsonResponse({'message': "Company code does not exist."}, status = 403)
                company_code = body_data['company_code']
                # 기타사항 입력 과 미입력 값 조정
                if 'etc' in body_data:
                    etc = body_data['etc']
                else:
                    etc = ''    

                # 새로운 입고확인서 생성
                new_order = InboundOrder.objects.create(
                    user_id = user.id,
                    company_code =  body_data['company_code'],
                    etc = etc
                ) 

                new_order_id = new_order.id

                
                for product_code in body_data.keys():
                    # 입력된 값중 길이가 7 = 시리얼 코드
                    if str(product_code[0:4]).isupper() == 4:
                        product_code = product_code # 시리얼 코드안에 있는 가격, 수량 정보 가져옴
                        print(product_code)
                        price = body_data[product_code]['price']
                        quantity = body_data[product_code]['Q']
                        # 제품 정보 테이블에서 시리얼 코드가 있는지 확인
                        if not ProductInfo.objects.filter(product_code__contains = product_code).exists():
                            raise Exception(f'{product_code} 가 존재하지 않습니다')
                        # 입고확인서 ID를 입력하여 입고된 상품의 정보 테이블에 저장
                        InboundQuantity.objects.create(
                            inbound_order_id = new_order_id,
                            product_code = product_code,
                            inbound_price = price,
                            inbound_quntity = quantity
                        )
                        # 입고된 내용을 통해 제품 history, 제품 회사 - 가격 테이블 생성 (바코드 생성 및 저장)
                        product_history_generator(product_code, quantity, price, etc)
                        update_product_his(product_code) # 기존에 있는 수량과 입고된 수량 파악 후 저장.
                        update_price(product_code, price, company_code)

            return JsonResponse({'message' : 'Inbounding processing has been completed.'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)
        except Exception as e:
            return JsonResponse({'message' : 'An exception occurred while running.'}, status = 403)

class CreateOutboundOrderView(View):
    @jwt_decoder
    @check_status
    def post(self, request):
        input_data = json.loads(request.body) # 여기서는 request.body를 사용
        user = request.user
        try:
            with transaction.atomic():
                #input_data 에서 받은 값에 company_code가 들어있는지 체크
                if not 'company_code' in input_data:
                    return JsonResponse({'message': "Company code does not exist."}, status = 403)
                
                #input_data 에서 받은 값으로 새로운 출고 주문서 생성
                new_OB_order = OutboundOrder.objects.create(
                    user_id = user.id,
                    company_code = input_data['company_code'],
                    etc = input_data['etc']
                )
    
                new_OB_order_id = new_OB_order.id

                
                for product_code in input_data.keys():
                    # 길이가 7인 값 = 시리얼 코드
                    if len(product_code) == 7:
                        product_code = product_code
                        price = input_data[product_code]['price']
                        quantity = input_data[product_code]['Q']

                        # 제품 정보 테이블에서 시리얼 코드를 검색 없으면 예외를 일으켜 트랜젝션 작동
                        if not ProductInfo.objects.filter(product_code__icontains = product_code).exists():
                            raise Exception(f'{product_code} 가 존재하지 않습니다')
                        # 제품이 있으면 수량, 가격, 생성한 출고 id로 OutboundQunatity 테이블 생성 
                        OutboundQuantity.objects.create(
                            outbound_order_id = new_OB_order_id,
                            product_code = product_code,
                            outbound_price = price,
                            outbound_quantity = quantity
                        )

                # ConfirmOutboundOrderView 에서 사용할 딕셔너리 생성
                Confirm_query = OutboundQuantity.objects.filter(outbound_order = new_OB_order_id).values('product_code', 'outbound_quantity')
                check_product_code = {}

                for query in Confirm_query:
                    product_code = query['product_code']
                    quantity    = query['outbound_quantity']
                    check_product_code[product_code] = int(quantity)

                
            return JsonResponse({"product_codes" : check_product_code }, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)
        except Exception as e:
            return JsonResponse({'message' : 'An exception occurred while running.'}, status = 403)

class ConfirmOutboundOrderView(View):
    @jwt_decoder
    @check_status
    def post(self, request):
        input_data = json.loads(request.body)
        try:
            with transaction.atomic():
                OB_id = input_data['OB_id']
                company_code = OutboundOrder.objects.get(id = OB_id).company_code

                # {프로덕트 코드 : 바코드 수량} 비교 딕셔너리 생성.
                product_codes_dic = {}
                check_status = OutboundQuantity.objects.filter(outbound_order_id = OB_id).values('product_code', 'outbound_quantity')
                for i in range(len(check_status)):
                    product_codes_dic[check_status[i]['product_code']] = check_status[i]['outbound_quantity']

                barcodes = input_data['barcodes']
                
                # 바코드를 슬라이싱해 프로덕트 코드화 딕셔너리 key 값에 슬라이싱한 바코드를 넣어 {프로덕트 코드 : 바코드 수량} 딕셔너리 값을 하나 차감.
                for i in range(len(barcodes)):
                    slicing_product_code = barcodes[i][:7]

                    if not slicing_product_code in product_codes_dic.keys():
                        return JsonResponse({'message' : 'Please check the first 7 digits of the product code.'}, status = 403 )
                    product_codes_dic[slicing_product_code] = int(product_codes_dic[slicing_product_code]) - 1
                
                # {프로덕트 코드 : 바코드 수량} 바코드 수량이 0이 되지않으면 (즉, 같은 딕셔너리에 포함된 같은 프로덕트 코드 값의 바코드가 들어오지 않았음) return 값 작동.
                for i in product_codes_dic.values():
                    if not i == 0:
                        return JsonResponse({"product_codes" : 'The barcode entered and the outbounding order do not match.' }, status = 200)
                
                for barcode in barcodes:
                    # 바코드 검증 use_status가 1이 아니면 return 값 작동.
                    if not ProductHis.objects.get(barcode = barcode).use_status == 1 :
                        return JsonResponse({'message' : 'Barcode already used.'}, status = 403 )
                    product_code = barcodes[i][:7]
                    
                    # 사용한 바코드 use_status 변경(사용함 = 2) 
                    # OutboundBarcode Table에 OB 아이디와 바코드 저장 부품 추적시 사용.
                    ProductHis.objects.filter(barcode = barcode).update(use_status = 2)
                    OutboundBarcode.objects.create(outbound_order_id = OB_id, barcode = barcode)
                    update_product_his(product_code)
                    
                     # 제품 정보에 수량 수정사항(사용 가능한 수량, 회사 - 출고 가격) 반영.
                    outbound_price = OutboundQuantity.objects.get(product_code = product_code, outbound_order_id = OB_id).outbound_price
                    update_product_his(product_code)
                    update_price(product_code, outbound_price, company_code)
                    
            return JsonResponse({"product_codes" : 'processing completed.' }, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)

class CreateSetInfoView(View):
    def __init__(self):
        # 날짜 설정
        now = datetime.now()
        self.year    = str(now.year)
        self.month   = str(now.month)
        self.day     = str(now.day) 

    def serial_generator(self, pg_code):
        product_group  = ProductGroup.objects.filter(code = pg_code)
        
        # 제품 그룹이 있는지 체크
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')

        CPPG = 'EX' + pg_code # SSPP 
        # 형번을 생성 등록된 제품 정보를 참고해 CPPG 가 존재하면 그 다음 형번을 부여 없으면 1로 시작.
        if SetProductInfo.objects.filter(set_product_code__icontains = CPPG).exists():
            latest_product_code = SetProductInfo.objects.filter(set_product_code__icontains = CPPG).latest('created_at').set_product_code
            model_number = int(latest_product_code[5:7]) + 1
        else:
            model_number = 1

        model_number = str(model_number).zfill(3)
        # 제품 시리얼 코드 생성 SSPP001
        set_code = CPPG + model_number
        
        return set_code


    def post(self, request):
        input_data = json.loads(request.body)
        set_code = self.serial_generator(input_data['pgcode'])
        
        try:
            new_set = SetProductInfo.objects.create(
                set_code = set_code,
                quantity = input_data['quantity'],
                safe_quantity = input_data['safe_quantity'],
                search_word = input_data['search_word'],
                name = input_data['name']
                )
            
            product_codes = input_data['product_code']
            for product_code in product_codes:
                quantity = int(product_codes[product_code])
                if not ProductInfo.objects.filter(product_code__icontains = product_code).exists():
                    raise Exception(f'{product_code} 가 존재하지 않습니다')
                
                SetProductQuantity.objects.create(
                    set_code = set_code,
                    product_code = product_code,
                    product_quantity = quantity
                )


            product_history_generator(set_code, input_data['quantity'],input_data['price'] ,input_data['etc'] )


            return JsonResponse({'mesaage' : 'Product information has been registered.'}, status = 200) 
        except KeyError:
            return JsonResponse({'mesaage' : 'Key Error'}, status = 403) 