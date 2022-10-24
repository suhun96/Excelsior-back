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

class CreateProductView(View):
    def __init__(self):
        # 날짜 설정
        now = datetime.now()
        self.year    = str(now.year)
        self.month   = str(now.month)
        self.day     = str(now.day) 

    def serial_generator(self, pg_id, cp_id, quantity, search_word, price, safe_quantity, etc):
        product_group  = ProductGroup.objects.filter(id = pg_id)
        company        = Company.objects.filter(id = cp_id)
        filter_product = Product.objects.filter(Q(product_group = pg_id) & Q(company = cp_id))
        
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')

        if company.exists() == False:
            raise ValueError('Company (trade name) that does not exist.')

        new_model_number = 1

        if filter_product.exists() == True:
            model_number = Product.objects.latest('created_at')
            new_model_number = model_number.model_number + 1

        
        
        model_number = str(new_model_number).zfill(3)

        pg_code  = ProductGroup.objects.get(id = pg_id).code
        
        cp_code   = Company.objects.get(id = cp_id).code

        product_serial_code = cp_code + pg_code + model_number
        # 제품 갯수만큼 시리얼 생성
        plus_quantity = int(quantity) + 1
        
        serial_code = cp_code + pg_code + model_number

        for i in range(1, plus_quantity):
            zero_num = str(i).zfill(3)
            serial_code2 = serial_code + zero_num + self.year[2:4] + self.month + self.day
            
            Product.objects.create(
                product_group_id    = pg_id,
                company_id          = cp_id,
                use_status_id       = 1,
                serial_code         = serial_code2,
                search_word         = search_word,
                price               = price,
                safe_quantity       = safe_quantity,
                model_number        = new_model_number,
                etc                 = etc
            )
        
        return product_serial_code 

    # @jwt_decoder
    # @check_status 
    def post(self, request):
        input_data = request.POST
        
        # serial_generator(self, pg_id, cp_id, quantity, search_word, price, safe_quantity)
        try: 
            transaction.atomic()
            product_serial_code = self.serial_generator(
                input_data['product_group_id'], input_data['company_id'],
                input_data['quantity'], input_data['search_word'],
                input_data['price'], input_data['safe_quantity'], input_data['etc'])

            check_quantity = Product.objects.filter(serial_code__contains = product_serial_code).count()
            
            ProductQuantity.objects.create(
                product_serial_code = product_serial_code,
                quantity  = check_quantity
            )

            return JsonResponse({'message': product_serial_code}, status = 200)

        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class UpdateProductView(View):
    def __init__(self):
        # 날짜 설정
        now = datetime.now()
        self.year    = str(now.year)
        self.month   = str(now.month)
        self.day     = str(now.day) 

    def post(self, request):
        input_data = request.POST
        serial_num = request.POST['serial_code']
        quantity   = request.POST['quantity']
        
        # 제품 코드 형식 확인
        if not len(serial_num) == 7:
            return JsonResponse({'message' : 'Please check the serial number.'} , status = 403)
        
        # 제품 코드 슬라이싱
        company_code        = serial_num[0:2]
        product_group_code  = serial_num[2:4]
        model_number        = serial_num[4:7]
        
        try:
            if not ProductQuantity.objects.filter(product_serial_code = serial_num).exists:
                return JsonResponse({'message' : 'No product exists.'}, status = 403)
            
            pg_code_id = ProductGroup.objects.get(code = product_group_code).id
            cp_code_id = Company.objects.get(code = company_code).id
            
            before_quantity = Product.objects.filter(serial_code__icontains = serial_num).count()
            
            choice_product = Product.objects.filter(product_group_id = pg_code_id, company_id = cp_code_id, model_number = model_number).last()

            for i in range(1, int(input_data['quantity']) + 1):
                zero_num = str(i + before_quantity).zfill(3)
                serial_code2 = company_code + product_group_code + model_number + zero_num + self.year[2:4] + self.month + self.day
            
                Product.objects.create(
                    product_group_id    = pg_code_id,
                    company_id          = cp_code_id,
                    use_status_id       = 1,
                    serial_code         = serial_code2,
                    search_word         = choice_product.search_word,
                    price               = input_data['price'],
                    safe_quantity       = choice_product.safe_quantity,
                    model_number        = model_number,
                    etc                 = input_data['etc']
                )
            
            # 제품 생성 갯수 카운팅
            after_quantity = Product.objects.filter(serial_code__contains = serial_num).count()
            
            # 입고 수량 정정
            ProductQuantity.objects.filter(product_serial_code = serial_num).update(quantity  = after_quantity)
            
            return JsonResponse({'message': f'{quantity}, {serial_num} products have been added.'}, status = 200)

        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)

class CreateWarehousingOrder(models.Model):
    def __init__(self):
        # 날짜 설정
        now = datetime.now()
        self.year    = str(now.year)
        self.month   = str(now.month)
        self.day     = str(now.day) 

    # @jwt_decoder
    # @check_status
    def post(self, request):
        input_data = request.POST
        serial_num = request.POST['serial_code']
        quantity   = request.POST['quantity']
        user       = request.user

        # 제품 코드 형식 확인
        if not len(serial_num) == 7:
            return JsonResponse({'message' : 'Please check the serial number.'} , status = 403)
        
        # 제품 코드 슬라이싱
        company_code        = serial_num[0:2]
        product_group_code  = serial_num[2:4]
        model_number        = serial_num[4:7]

        if not Company.objects.filter(code = company_code).exists():
            return JsonResponse({'message' : '회사 코드 없음'}, status = 403)
        
        if not ProductGroup.objects.filter(code = product_group_code).exists():
            return JsonResponse({'message' : '제품 코드 없음'}, status = 403)
        
        WarehousingOrder.objects.create(
            user_id     = user.id, 
            product_id  = input_data['product_id'],
            company_id  = input_data['company_id'],
            inbound_price   = input_data[''],
            inbound_quntity = input_data[''],
            inbound_address = input_data['']
        )