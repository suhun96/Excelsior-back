import json
from venv import create
from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from django.db.models   import Q
from datetime           import datetime

# Model
from users.models       import *
from products.models    import *
from users.jwtdecoder   import jwt_decoder
from users.checkstatus  import check_status

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
                return JsonResponse({'messaga' : 'The product name(product code) is already registered.'}, status = 403)      

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
                return JsonResponse({'messaga' : 'The product name(product code) is already registered.'}, status = 403)      

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
        
        
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')

        if company.exists() == False:
            raise ValueError('Company (trade name) that does not exist.')

        CPPG = cp_code + pg_code
        if ProductInfo.objects.filter(serial_code__icontains = CPPG).exists():
            latest_serial_code = ProductInfo.objects.filter(serial_code__icontains = CPPG).latest('created_at').serial_code
            model_number = int(latest_serial_code[5:7]) + 1
        else:
            model_number = 1

        model_number = str(model_number).zfill(3)

        product_serial_code = cp_code + pg_code + model_number
        print(f'시리얼 코드 생성 완료 {product_serial_code}')

        print('새로운 시리얼 코드 DB에 생성')
        return product_serial_code

    def product_history_generator(self, product_serial_code, quantity, price ,etc):
        try:
            product_his = ProductHis.objects.filter(serial_code = product_serial_code)
            if product_his.exists():
                before_quantity = product_his.count()
                print(before_quantity)
                
                for i in range(1 , quantity +1):
                    zero_num = str(i + before_quantity).zfill(3)
                    barcode = product_serial_code + zero_num + self.year[2:4] + self.month + self.day
                    
                    ProductHis.objects.create(
                        use_status = 1,
                        serial_code = product_serial_code,
                        price = price,
                        barcode = barcode,
                        etc = etc
                    )

                return print('기존 제품을 참고하여 히스토리 생성완료')
            else:
                for i in range(1, int(quantity) + 1):
                    zero_num = str(i).zfill(3)
                    barcode = product_serial_code + zero_num + self.year[2:4] + self.month + self.day

                    ProductHis.objects.create(
                    use_status = 1,
                    serial_code = product_serial_code,
                    price = price,
                    barcode = barcode,
                    etc = etc)

                return print('새로운 제품 히스토리 생성완료')
        except KeyError:
            return JsonResponse({'message' : '키 에러'}, status = 403)
     
    def post(self, request):
        input_data = request.POST

        try:
            product_serial_code = self.serial_generator(input_data['pg_code'], input_data['cp_code'])
            
            print(product_serial_code)

            product_info = ProductInfo.objects.create(
                serial_code = product_serial_code,
                quantity = input_data['quantity'],
                safe_quantity = input_data['safe_quantity'],
                search_word = input_data['search_word'],
                name = input_data['name']
                )


            # def product_history_generator(self, product_info_id, quantity, product_serial_code, price ,etc):
            self.product_history_generator(product_serial_code, input_data['quantity'],input_data['price'] ,input_data['etc'] )

            return JsonResponse({'mesaage' : '제품 정보가 등록되었습니다.'}, status = 200) 
        except KeyError:
            return JsonResponse({'message' : 'Key error'}, status = 403)

class CreateInboundOrderView(View):
    @jwt_decoder
    @check_status
    def post(self, request):
        # form_data = request.POST
        body_data= json.loads(request.body)
        user = request.user
        
        if not 'company_code' in body_data:
                return JsonResponse({'message': "company_code X"}, status = 403)
        company_code = body_data['company_code']

        if 'etc' in body_data:
            etc = body_data['etc']
        else:
            etc = ''    

        new_order = InboundOrder.objects.create(
            user_id = user.id,
            company_code =  body_data['company_code'],
            etc = body_data['etc']
        ) 

        new_order_id = new_order.id

        for key in body_data.keys():
            if len(key) == 7:
                price = body_data[key]['price']
                quantity = body_data[key]['Q']
                InboundQuantity.objects.create(
                    inbound_order_id = new_order_id,
                    serial_code = key,
                    inbound_price = price,
                    inbound_quntity = quantity
                )
        
        return JsonResponse({'message' : 'check'}, status = 200)