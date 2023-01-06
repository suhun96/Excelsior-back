import json, re


from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection, IntegrityError
from django.db.models   import Q, Sum


# Model
from users.models       import *
from products.models    import *
from companies.models   import *
from locations.models   import *
from stock.models       import *

# decorator & utills 
from users.decorator    import jwt_decoder
from products.utils     import *
from stock.utils        import *

import telegram
from my_settings        import TELEGRAM_TOKEN, CHAT_ID


class ProductGroupView(View):
    def get(self, request):
        name = request.GET.get('name', None)
        code = request.GET.get('code', None)
        status = request.GET.get('status', None)
        offset = int(request.GET.get('offset'))
        limit  = int(request.GET.get('limit'))

        length = ProductGroup.objects.all().count()

        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if code:
                q &= Q(code__icontains = code)
            if status:
                q &= Q(status = status)
            
            # result = list(ProductGroup.objects.filter(q).values())
            result = list(ProductGroup.objects.filter(q)[offset : offset+limit].values())
        
            return JsonResponse({'message' : result, 'length': length}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
            
    @jwt_decoder
    def post(self, request):
        input_data = request.POST

        
        if not "name" in input_data:
            return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

        if ProductGroup.objects.filter(name = input_data['name']).exists():
                return JsonResponse({'message' : 'The product name is already registered.'}, status = 403)

        if ProductGroup.objects.filter(code = input_data['code']).exists():
                return JsonResponse({'message' : 'The product code is already registered.'}, status = 403)     
        
        

        REGEX_CODE = '[A-Z]{2}'  

        CREATE_SET = {}
        CREATE_OPT = ['name', 'code', 'etc']
        # create_options 로 request.POST 의 키값이 정확한지 확인.
        for key in dict(request.POST).keys():
            if key in CREATE_OPT:
                if key == 'code':
                    if not re.fullmatch(REGEX_CODE, input_data['code']):
                        return JsonResponse({'message' : '제품 그룹 코드의 형식을 확인해주세요. [A-Z] 2자리 '}, status = 403)

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
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        group_id = request.GET.get('group_id')

        if not ProductGroup.objects.filter(id = group_id).exists():
            return JsonResponse({'message' : '존재하지 않는 제품그룹입니다.'}, status = 403)

        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['etc', 'status']

                for key, value in input_data.items():
                    if key == 'name':
                        if ProductGroup.objects.filter(name = value).exists():
                            return JsonResponse({'message' : 'The product name is already registered.'}, status = 403)
                        else:
                            UPDATE_SET.update({ key : value })

                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    
                ProductGroup.objects.filter(id = group_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class ProductInfoView(View):
    def create_sheet_new(self, input_data, user, new_product):
        user = user
        input_user =  user.id
        input_data = input_data
        company_id = input_data.get('company_id', None)

        if not company_id:
            company_id = 1
        
        price    = input_data.get('price', None)
        quantity = input_data.get('quantity', None)
        new_product_code = new_product.product_code

        try:
            with transaction.atomic():
        
                if company_id:
                    new_sheet = Sheet.objects.create(
                        user_id = input_user,
                        type = 'new',
                        company_id = company_id,
                        etc  = '초도 입고'
                    )
                            
                    if Product.objects.filter(product_code = new_product_code).exists() == False:
                        raise Exception({'message' : f'{new_product_code}는 존재하지 않습니다.'}) 
                
                    SheetComposition.objects.create(
                        sheet_id        = new_sheet.id,
                        product_id      = new_product.id,
                        quantity        = quantity, 
                        warehouse_code  = Warehouse.objects.get(main = True).code,
                        location        = new_product.location,
                        unit_price      = price,
                    )
                    
                    stock = StockByWarehouse.objects.filter(warehouse_code = Warehouse.objects.get(main = True).code , product_id = new_product.id)
            
                    if stock.exists():
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity + int(quantity)
                    else:
                        stock_quantity  = int(quantity)
                    
                    StockByWarehouse.objects.filter(warehouse_code = Warehouse.objects.get(main = True).code, product_id = new_product.id).create(
                        sheet_id = new_sheet.id,
                        stock_quantity = stock_quantity,
                        product_id = new_product.id,
                        warehouse_code = Warehouse.objects.get(main = True).code )
                    
                    # mam_create_sheet(new_product.id, price, quantity, stock_quantity)

                    QuantityByWarehouse.objects.filter(warehouse_code = Warehouse.objects.get(main = True).code, product_id = new_product.id).update_or_create(
                        product_id = new_product.id,
                        warehouse_code = Warehouse.objects.get(main = True).code,
                        defaults={
                            'total_quantity' : stock_quantity,
                        })
                    
                    if Product.objects.get(id = new_product.id).is_serial == True:
                        create_product_serial_code(new_product.id, quantity, new_sheet.id)    
                    else:
                        pass
                
                else:
                    new_sheet = Sheet.objects.create(
                        user_id = input_user,
                        company_id =  company_id,
                        type = 'new',
                        etc  = '초도 입고'
                    )
                            
                    if Product.objects.filter(product_code = new_product_code).exists() == False:
                        raise Exception({'message' : f'{new_product_code}는 존재하지 않습니다.'}) 
                
                    SheetComposition.objects.create(
                        sheet_id        = new_sheet.id,
                        product_id      = new_product.id,
                        quantity        = quantity, 
                        warehouse_code  = Warehouse.objects.get(main = True).code,
                        location        = new_product.location,
                        unit_price      = price,
                    )
                    
                    stock = StockByWarehouse.objects.filter(warehouse_code = Warehouse.objects.get(main = True).code , product_id = new_product.id)
                    
                    if stock.exists():
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity + int(quantity)
                    else:
                        stock_quantity  = int(quantity)

                    StockByWarehouse.objects.filter(warehouse_code = Warehouse.objects.get(main = True).code, product_id = new_product.id).create(
                        sheet_id = new_sheet.id,
                        stock_quantity = stock_quantity,
                        product_id = new_product.id,
                        warehouse_code = Warehouse.objects.get(main = True).code )
                    
                    # mam_create_sheet(new_product.id, price, quantity, stock_quantity)
                    
                    QuantityByWarehouse.objects.filter(warehouse_code = Warehouse.objects.get(main = True).code, product_id = new_product.id).update_or_create(
                        product_id = new_product.id,
                        warehouse_code = Warehouse.objects.get(main = True).code,
                        defaults={
                            'total_quantity' : stock_quantity
                        })
                    # 초도 입고 시리얼 코드 생산

                    if Product.objects.get(id = new_product.id).is_serial == True:
                        create_product_serial_code(new_product.id, quantity, new_sheet.id)    
                    else:
                        pass

        except:
            raise Exception({'message' : 'sheet를 생성하는중 에러가 발생했습니다.'})

    def get(self, request):
        offset = int(request.GET.get('offset'))
        limit  = int(request.GET.get('limit'))

        length = Product.objects.all().count()


        name                = request.GET.get('name', None)
        keyword             = request.GET.get('keyword', None)
        productgroup_code   = request.GET.get('product_group_code', None)
        warehouse_code      = request.GET.get('warehouse_code', None)
        product_code        = request.GET.get('product_code', None)
        barcode             = request.GET.get('barcode', None)
        status              = request.GET.get('status', None)
        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if keyword:
                q &= Q(keyword__icontains = keyword)
            if productgroup_code:
                q &= Q(productgroup_code__icontains = productgroup_code)
            if warehouse_code:
                q &= Q(warehouse_code__icontains = warehouse_code)
            if product_code:
                q &= Q(product_code__icontains = product_code)
            if barcode:
                q &= Q(barcode__icontains = barcode)
            if status:
                q &= Q(status = status)

            result_list = []
            products = Product.objects.filter(q)[offset : offset+limit].values()
            
            for product in products:
                if product['company_code']== '':
                    dict_t = {
                        'id' : product['id'],
                        'is_set' : product['is_set'],
                        'is_serial' : product['is_serial'],
                        'company_code'      : '',
                        'company_name'      : '',
                        'productgroup_code' : product['productgroup_code'],
                        'productgroup_name' : ProductGroup.objects.get(code = product['productgroup_code']).name,
                        'product_num'       : product['product_num'],
                        'product_code'      : product['product_code'],
                        'safe_quantity'     : product['safe_quantity'],
                        'keyword'           : product['keyword'],
                        'name'              : product['name'],
                        'warehouse_code'    : product['warehouse_code'],
                        'warehouse_name'    : Warehouse.objects.get(code = product['warehouse_code']).name,
                        'location'          : product['location'],
                        'barcode'           : product['barcode'],
                        'status'            : product['status'],
                    }
                    result_list.append(dict_t)
                    
                else:
                    dict_t = {
                        'id' : product['id'],
                        'is_set' : product['is_set'],
                        'is_serial' : product['is_serial'],
                        'company_code'      : product['company_code'],
                        'company_name'      : Company.objects.get(code = product['company_code']).name,
                        'productgroup_code' : product['productgroup_code'],
                        'productgroup_name' : ProductGroup.objects.get(code = product['productgroup_code']).name,
                        'product_num'       : product['product_num'],
                        'product_code'      : product['product_code'],
                        'safe_quantity'     : product['safe_quantity'],
                        'keyword'           : product['keyword'],
                        'name'              : product['name'],
                        'warehouse_code'    : product['warehouse_code'],
                        'warehouse_name'    : Warehouse.objects.get(code = product['warehouse_code']).name,
                        'location'          : product['location'],
                        'barcode'           : product['barcode'],
                        'status'            : product['status'],
                    }
                    result_list.append(dict_t)


            return JsonResponse({'message' : result_list, 'length': length}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'keyerror'}, status = 403)

    @jwt_decoder
    def post(self, request):
        user = request.user
        input_data = json.loads(request.body)
        name = input_data.get('name', None)
        product_group_code = input_data.get('product_group_code', None)
        warehouse_code = input_data.get('warehouse_code', None)
        company_code = input_data.get('company_code', None)
        is_set = input_data.get('is_set', None)
        composition = input_data.get('composition', None )
        is_serial = input_data.get('is_serial', None)


        check_price    = input_data.get('price', None)
        check_quantity = input_data.get('quantity', None)
        
        
        
        # 필수값 제품명 확인
        if name == None:
            return JsonResponse({'message' : '제품명을 입력해주세요'}, status = 403)

        if product_group_code == None:
            return JsonResponse({'message' : '제품 그룹 코드를 입력해주세요'}, status = 403)
        else:
            if not ProductGroup.objects.filter(code = product_group_code).exists():
                return JsonResponse({'message' : '존재하지 않는 제품그룹 코드입니다.'}, status = 403)
        
        if warehouse_code:
            if not Warehouse.objects.filter(code = input_data['warehouse_code']).exists():
                return JsonResponse({'message' : '존재하지 않는 창고 코드입니다.'}, status = 403)
        if not warehouse_code:
            warehouse_code = Warehouse.objects.get(main = True).code
        
        # 시리얼 사용 유무
        if not is_serial:
            is_serial = False
        if is_serial:
            is_serial = True

        try:
            with transaction.atomic():
                # 회사코드가 있으면
                if company_code:
                # 회사코드 체크
                    if not Company.objects.filter(code = company_code).exists():
                        return JsonResponse({'message' : f'[{company_code}] 존재하지 않는 회사 코드입니다.'})
                    
                    product = Product.objects.filter(productgroup_code = product_group_code) 

                    if product.exists():
                        productgroup_num = product.latest('created_at').product_num
                        change_int_num = int(productgroup_num) + 1
                        product_num = str(change_int_num).zfill(3)           
                    else:
                        product_num = '001'
                    
                    # 세트 상품이면 
                    if is_set == "True":
                        CREATE_SET = {
                            'is_set' : True,
                            'is_serial': True,      
                            'productgroup_code' : product_group_code , 
                            'company_code' : company_code, 
                            'name' : name,
                            'product_num'  : product_num,
                            'product_code' : company_code + product_group_code + product_num,
                            'warehouse_code' : warehouse_code
                        }
                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['keyword', 'location', 'barcode']:
                                CREATE_SET.update({key : value})

                            if key == 'safe_quantity':
                                if value == "":
                                    CREATE_SET.update({key : 0})
                                else:
                                    CREATE_SET.update({key : value}) 
                                
                        
                        # 새로운  세트 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)

                        if check_price and check_quantity:
                            self.create_sheet_new(input_data, user, new_product)
                        
                        # 새로운 세트 제품의 구성품 등록
                        for id, quantity in composition.items():
                            ProductComposition.objects.create(
                                set_product_id = new_product.id,
                                composition_product_id = id,
                                quantity = quantity
                            )
                        return JsonResponse({'message' : '[Case 1] 새로운 세트 상품이 등록되었습니다.'}, status = 200) 
                    # 일반 상품이면
                    else:
                        CREATE_SET = {
                            'is_set' : False,
                            'is_serial' : is_serial,  
                            'productgroup_code' : product_group_code , 
                            'company_code'      : company_code, 
                            'name'              : name,
                            'product_num'       : product_num,
                            'product_code'      : company_code + product_group_code + product_num,
                            'warehouse_code'    : warehouse_code
                        }

                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['keyword', 'location','barcode']:
                                CREATE_SET.update({key : value})

                            if key == 'safe_quantity':
                                if value == "":
                                    CREATE_SET.update({key : 0})
                                else:
                                    CREATE_SET.update({key : value})
                        
                        # 새로운 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)
                        
                        if check_price and check_quantity:
                            self.create_sheet_new(input_data, user, new_product)

                        return JsonResponse({'message' : '[Case 2] 새로운 일반 상품이 등록되었습니다'}, status = 200) 
                    
                # 회사코드가 없으면 
                if not company_code:
                    product = Product.objects.filter(productgroup_code = product_group_code) 

                    if product.exists():
                        productgroup_num = product.latest('created_at').product_num
                        change_int_num = int(productgroup_num) + 1
                        product_num = str(change_int_num).zfill(3)           
                    else:
                        product_num = '001'
                    
                    # 세트 상품이면 
                    if is_set == "True":
                        CREATE_SET = {
                            'is_set' : True,  
                            'is_serial' : True,
                            'productgroup_code' : product_group_code ,  
                            'name' : name,
                            'product_num' : product_num,
                            'product_code' : product_group_code + product_num,
                            'warehouse_code' : warehouse_code
                        }
                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['keyword', 'location','barcode']:
                                CREATE_SET.update({key : value})
                            
                            if key == 'safe_quantity':
                                if value == "":
                                    CREATE_SET.update({key : 0})
                                else:
                                    CREATE_SET.update({key : value})
                        
                        # 새로운  세트 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)

                        if check_price and check_quantity:
                            self.create_sheet_new(input_data, user, new_product)

                        # 새로운 세트 제품의 구성품 등록
                        for id, quantity in composition.items():
                            ProductComposition.objects.create(
                                set_product_id = new_product.id,
                                composition_product_id = id,
                                quantity = quantity
                            )
                        return JsonResponse({'message' : '[Case 3] 새로운 세트 상품이 등록되었습니다.'}, status = 200) 
                    # 일반 상품이면
                    else:
                        CREATE_SET = {
                            'is_set' : False,
                            'is_serial' : is_serial,  
                            'productgroup_code' : product_group_code,  
                            'name' : name,
                            'product_num' : product_num,
                            'product_code' : product_group_code + product_num,
                            'warehouse_code' : warehouse_code
                        }
                        
                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['keyword', 'location','barcode']:
                                CREATE_SET.update({key : value})

                            if key == 'safe_quantity':
                                if value == "":
                                    CREATE_SET.update({key : 0})
                                else:
                                    CREATE_SET.update({key : value})
                        
                        # 새로운 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)
                        
                        if check_price and check_quantity:
                            self.create_sheet_new(input_data, user, new_product)
                        
                        return JsonResponse({'message' : '[Case 4] 새로운 일반 상품이 등록되었습니다.'}, status = 200)

        except KeyError:
            return JsonResponse({'message' : 'composition에 입력된 id 값을 확인해주세요'}, status = 403)        

class ModifyProductInfoView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        product_id = input_data.get('id', None)
        
        if not product_id:
            return JsonResponse({'message' : "수정할 Product id가 입력되지 않았습니다."}, status = 403)
        if Product.objects.filter(id = product_id).exists() == False:
            return JsonResponse({'message' : "존재하지 않는 제품입니다."}, status = 403)
        
        UPDATE_SET = {}
        UPDATE_OPT = ['safe_quantity', 'keyword', 'name', 'location', 'barcode']

        try:
            with transaction.atomic():

                for key, value in input_data.items():
                    if key == 'warehouse_code':
                        if not Warehouse.objects.filter(code = value).exists():
                            return JsonResponse({'message' : '존재하지 않는 창고 코드입니다.'}, status = 403)
                        UPDATE_SET.update({key : value})

                    if key in UPDATE_OPT:
                        UPDATE_SET.update({key : value})
                
                Product.objects.filter(id = product_id).update(**UPDATE_SET)

                return JsonResponse({'message' : 'Check update'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

#------------------------------------------------------------------------------------------------------#

class CreateProductEtcTitleView(View):
    def post(self, request):
        title   = request.POST['title']

        try:
            new_custom_title = ProductEtcTitle.objects.create(
                title = title,
                status = True
            )
        
            return JsonResponse({'message' : 'product etc title 생성 성공'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '잘못된 key 값을 입력하셨습니다.'}, status = 403)

class ModifyProductEtcTitleView(View):
    def post(self, request):
        id      = request.POST['product_title_id']
        
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
            ProductEtcTitle.objects.filter(id = id).update(**UPDATE_SET)
            
            return JsonResponse({'message' : 'product etc title 수정을 성공했습니다.'}, status = 200)
        except ProductEtcTitle.DoesNotExist:
            return JsonResponse({'message' : f'title id를 확인해주세요. {id}'}, status = 403)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)  

class InquireProductEtcTitleView(View):
    def get(self, request):

        Title_list = list(ProductEtcTitle.objects.all().values())

        return JsonResponse({'message': Title_list}, status = 200)

class InquireProductEtcDescView(View):
    def get(self, request):
        product_id = request.GET.get('product_id')
        Use_Titles = ProductEtcTitle.objects.filter(status = True).values_list('id', flat= True)
        result = []
        for title_id in Use_Titles:
            try:
                contents = ProductEtcDesc.objects.get(product_id = product_id, etc_title_id = title_id).contents
                dict = {}
                dict.update({
                    "title_id" : title_id,
                    "contents" : contents
                })
                result.append(dict)
            except ProductEtcDesc.DoesNotExist:
                pass

        return JsonResponse({'message' : result}, status = 200)

class CreateProductEtcDescView(View):
    def post(self, request):
        etc_title_id    = request.POST['title_id']
        product_id      = request.POST['product_id']
        desc            = request.POST['desc']

        try:
            new_custom_value, check  = ProductEtcDesc.objects.update_or_create(
                product_id = product_id,
                etc_title_id = etc_title_id,
                defaults={
                    'contents' : desc
                })
            if check == True:
                return JsonResponse({'message' : '생성 성공'}, status = 200)
            else:
                return JsonResponse({'message' : '수정 성공'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '잘못된 key 값을 입력하셨습니다.'}, status = 200)

###########################################################################################################

class SetInfoView(View):
    def get(self, request):
        product_code = request.GET.get('product_code', None)

        if not product_code:
            return JsonResponse({'message' : 'product_code를 입력해주세요'})
        
        product_id = Product.objects.get(product_code = product_code).id

        if Product.objects.get(id = product_id).is_set == 0:
            return JsonResponse({'message' : '세트 상품이 아닙니다.'})

        composition = ProductComposition.objects.filter(set_product_id = product_id )

        result_list = []
        
        for object in composition:
            composition_product_id = object.composition_product.id
            composition_product_quantity = object.quantity

            product = Product.objects.get(id = composition_product_id)

            dict_W = {}
            
            warehouse_list = QuantityByWarehouse.objects.filter(product_id = composition_product_id).values()
                       
            for object in warehouse_list:
                dict_W[object['warehouse_code']] = object['total_quantity']

            if product.company_code== '':
                dict_t = {
                    'id'                : product.id,
                    'is_set'            : product.is_set,
                    'company_code'      : '',
                    'company_name'      : '',
                    'productgroup_code' : product.product_code,
                    'productgroup_name' : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'product_num'       : product.product_num,
                    'product_code'      : product.product_code,
                    'safe_quantity'     : product.safe_quantity,
                    'keyword'           : product.keyword,
                    'name'              : product.name,
                    'warehouse_code'    : product.warehouse_code,
                    'location'          : product.location,
                    'status'            : product.status,
                    'consumption'       : composition_product_quantity,
                    'stock'             : dict_W
                    }
                
                result_list.append(dict_t)
            else:
                dict_t = {
                    'id'                : product.id,
                    'is_set'            : product.is_set,
                    'company_code'      : product.company_code,
                    'company_name'      : Company.objects.get(code = product.company_code).name ,
                    'productgroup_code' : product.product_code,
                    'productgroup_name' : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'product_num'       : product.product_num,
                    'product_code'      : product.product_code,
                    'safe_quantity'     : product.safe_quantity,
                    'keyword'           : product.keyword,
                    'name'              : product.name,
                    'warehouse_code'    : product.warehouse_code,
                    'location'          : product.location,
                    'status'            : product.status,
                    'consumption'       : composition_product_quantity,
                    'stock'             : dict_W
                }
            
                result_list.append(dict_t)
        
        return JsonResponse({'message' : result_list}, status = 200)


class ProductStatusView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        user = request.user
        product_id = input_data.get('product_id', None)
        try:
            with transaction.atomic():

                if not product_id:
                    return JsonResponse({'message' : "product_id를 입력해주세요"}, status = 403)

                if user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)

                if input_data['status'] == "False":
                    Product.objects.filter(id = product_id).update( status = False)
                    return JsonResponse({'message' : '제품 상태 False'}, status = 200)
                
                if input_data['status'] == "True": 
                    Product.objects.filter(id = product_id).update( status = True)
                    return JsonResponse({'message' : '제품 상태 True'}, status = 200)

        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'}, status = 403)


class ProductGroupStatusView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        user = request.user
        product_group_id = input_data.get('product_group_id', None)
        try:
            with transaction.atomic():

                if not product_group_id:
                    return JsonResponse({'message' : "product_id를 입력해주세요"}, status = 403)

                if user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)

                if input_data['status'] == "False":
                    ProductGroup.objects.filter(id = product_group_id).update( status = False)
                    return JsonResponse({'message' : '제품 그룹 상태 False'}, status = 200)
                
                if input_data['status'] == "True": 
                    ProductGroup.objects.filter(id = product_group_id).update( status = True)
                    return JsonResponse({'message' : '제품 그룹 상태 True'}, status = 200)

        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'}, status = 403)