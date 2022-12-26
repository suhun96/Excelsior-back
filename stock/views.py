import json, re

import datetime

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from django.db.models   import Q , Sum

# Models
from stock.models       import *
from products.models    import *
from users.models       import *
from locations.models   import *


# deco
from users.decorator    import jwt_decoder
from products.utils     import telegram_bot


class NomalStockView(View):
    def price_checker(self, input_data):
        input_data = input_data
        input_products = input_data.get('products', None)
        input_company = input_data.get('company_code')

        try:
            with transaction.atomic():
                if input_data['type'] == 'inbound':
                    for product in input_products:
                        product_id = Product.objects.get(product_code =product['product_code']).id
                        ProductPrice.objects.update_or_create(
                            product_id = product_id,
                            company_code = input_company,
                            defaults={
                                'inbound_price' : product['price']
                            }
                        )
                        
                if input_data['type'] == 'outbound':
                    for product in input_products:
                        product_id = Product.objects.get(product_code =product['product_code']).id
                        ProductPrice.objects.update_or_create(
                            product_id = product_id,
                            company_code = input_company,
                            defaults={
                                'outbound_price' : product['price']
                            }
                        )
        except:
            raise Exception({'message' : 'price_checker를 생성하는중 에러가 발생했습니다.'})

    def create_sheet(self, input_data, user):
        user = user
        input_data = input_data

        input_user =  user.id
        input_type = input_data.get('type', None)
        input_etc  = input_data.get('etc', None)
        input_company = input_data.get('company_code', None)
        input_products = input_data.get('products', None)
        
        try:
            with transaction.atomic():
                new_sheet = Sheet.objects.create(
                    user_id = input_user,
                    type = input_type,
                    company_code = input_company,
                    etc  = input_etc
                )

                if not input_products:
                    raise Exception({'message' : '입,출고서에 제품을 비워 등록할 수 없습니다.'})
                

                for product in input_products:
                    product_code = product['product_code']
                    product_id   = Product.objects.get(product_code =product['product_code']).id

                    if Product.objects.filter(product_code = product_code).exists() == False:
                        raise Exception({'message' : f'{product_code}는 존재하지 않습니다.'}) 

                    new_sheet_composition = SheetComposition.objects.create(
                        sheet_id        = new_sheet.id,
                        product_id      = product_id,
                        quantity        = product['quantity'], 
                        warehouse_code  = product['warehouse_code'],
                        location        = product['location'],
                        unit_price      = product['price'],
                    )

                    if 'serial_code' in product:
                        for serial_code in product['serial_code']:
                            # 입/출고 구성품의 serial_code 연결
                            SerialInSheetComposition.objects.create(
                                sheet_composition = new_sheet_composition,
                                serial_code = serial_code
                            )
                            
                            # serial 추적
                            if SerialAction.objects.filter(serial = serial_code).exists():
                                # 12월 23일 중단점
                                # if SerialAction.objects.filter(serial_code).count() > 1:
                                    # raise Exception({'messgae' : f'{product_code}는 존재하지 않습니다.'})    
                                
                                actions = SerialAction.objects.get(serial = serial_code).actions
                                actions = actions + f',{new_sheet.id}'
                                Update_serial_action = SerialAction.objects.filter(serial = serial_code).update(actions = actions)
                            
                            else:
                                SerialAction.objects.create(
                                    serial = serial_code,
                                    product_id = product_id,
                                    actions = new_sheet.id
                                )

            return new_sheet
        except:
            raise Exception({'message' : 'sheet를 생성하는중 에러가 발생했습니다.'})

    def create_serial_code(self, composition, new_sheet_id):
        now = datetime.now()
        year    = str(now.year)
        month   = str(now.month).zfill(2)
        day     = str(now.day).zfill(2)
        today = year[2:4] + month + day

        product_id      = composition.product.id
        quantity        = composition.quantity

        product_code = Product.objects.get(id = product_id).product_code
        
        serial_code1 = product_code + today

       
        if not SerialAction.objects.filter(serial__icontains = serial_code1).exists():
            for i in range(quantity):
                route = '01'
                numbering = str(i + 1).zfill(3)
                serial_code2 = serial_code1 + route + numbering   
                SerialAction.objects.create(serial = serial_code2, create = new_sheet_id)
        else:
            last_serial = SerialAction.objects.filter(serial__icontains = serial_code1).latest('id').serial
            
            before_route = last_serial.replace(serial_code1, "")
            before_route = before_route[:2]
            
            after_route = int(before_route) + 1
            
            for i  in range(quantity):
                numbering = str(i + 1).zfill(3)
                serial_code2 = serial_code1 + str(after_route).zfill(2) + numbering
                SerialAction.objects.create(serial = serial_code2, create = new_sheet_id)
    
    @jwt_decoder
    def post(self, request):
        input_data = json.loads(request.body)
        user = request.user

        new_sheet = self.create_sheet(input_data, user)
        new_sheet_id = new_sheet.id

        try:
            with transaction.atomic():
                if new_sheet.type == 'inbound':
                    compositions = SheetComposition.objects.filter(sheet_id = new_sheet_id).values(
                            'product',
                            'unit_price',
                            'quantity',
                            'warehouse_code'
                        )

                    for composition in compositions:
                        product_id     = composition.get('product')
                        warehouse_code = composition.get('warehouse_code')
                        quantity       = composition.get('quantity') 
                        
                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                            stock_quantity  = before_quantity + int(quantity)
                        else:
                            stock_quantity  = int(quantity)

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = new_sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={
                                
                                'total_quantity' : stock_quantity,
                            })

                    self.price_checker(input_data)
                    telegram_bot(new_sheet_id)

                    return JsonResponse({'message' : '입고 성공'}, status = 200)

                if new_sheet.type == 'outbound':
                    compositions = SheetComposition.objects.filter(sheet_id = new_sheet_id).values(
                            'product',
                            'unit_price',
                            'quantity',
                            'warehouse_code'
                        )

                    for composition in compositions:
                        product_id     = composition.get('product')
                        warehouse_code = composition.get('warehouse_code')
                        quantity       = composition.get('quantity')
                        
                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                            stock_quantity  = before_quantity - int(quantity)
                        else:
                            stock_quantity  = int(quantity)

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = new_sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={
                                
                                'total_quantity' : stock_quantity,
                            })
                        
                    self.price_checker(input_data)
                    telegram_bot(new_sheet_id)
                    
                    return JsonResponse({'message' : '출고 성공'}, status = 200)

                if new_sheet.type == 'generate':
                    generated_composition = SheetComposition.objects.get(sheet_id = new_sheet_id)

                    product_id     = generated_composition.product.id
                    warehouse_code = generated_composition.warehouse_code
                    quantity       = generated_composition.quantity


                    # 재고 있는지 확인
                    stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                    
                    if stock.exists():
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity + int(quantity)
                    else:
                        stock_quantity  = int(quantity)

                    # 창고별 입고, 출고 내역 업데이트 
                    StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                        sheet_id = new_sheet_id,
                        stock_quantity = stock_quantity,
                        product_id = product_id,
                        warehouse_code = warehouse_code )
                    
                    # 창고별 제품 총 수량
                    QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                        product_id = product_id,
                        warehouse_code = warehouse_code,
                        defaults={
                            
                            'total_quantity' : stock_quantity,
                        })

                    # 소진 
                    used_sheet = Sheet.objects.create(
                        user_id = 1,
                        type = 'used',
                        company_code = 'EX',
                        etc = f'Sheet_ID :{new_sheet_id} 세트 생산으로 인한 재고소진'
                    )

                    set_compositions = ProductComposition.objects.filter(set_product_id = product_id).values()

                    for composition in set_compositions:
                        SheetComposition.objects.create(
                            sheet_id        = used_sheet.id,
                            product_id      = composition['composition_product_id'],
                            unit_price      = 333330,
                            quantity        = composition['quantity'],
                            warehouse_code  = warehouse_code,
                            location        = Product.objects.get(id = composition['composition_product_id']).location,
                            etc             = f'Sheet_ID : {new_sheet_id} 생산으로 인한 구성품 소진입니다.'
                        )

                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = composition['composition_product_id'])
                        
                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                            stock_quantity  = before_quantity - int(composition['quantity'])
                        else:
                            stock_quantity  = int(composition['quantity'])

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = composition['composition_product_id']).create(
                            sheet_id = used_sheet.id,
                            stock_quantity = stock_quantity,
                            product_id = composition['composition_product_id'],
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = composition['composition_product_id']).update_or_create(
                            product_id = composition['composition_product_id'],
                            warehouse_code = warehouse_code,
                            defaults={
                                
                                'total_quantity' : stock_quantity,
                            })
                    
                    # serial code 생선
                    self.create_serial_code(generated_composition, new_sheet_id)
                    serial_codes = SerialAction.objects.filter(create = new_sheet_id).values('serial')
                    serial_code_list = []
                    for serial_code in serial_codes:
                        serial_code_list.append(serial_code['serial'])
                    
                    return JsonResponse({'message' : '생산 성공', 'serial_list' : serial_code_list}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'keyerror'}, status = 403)

class QunatityByWarehouseView(View):
    def get(self, request):
        
        product_code_list = request.GET.getlist('product_code', None)
        
        list_A = []
        for product_code in product_code_list:
            product = Product.objects.get(product_code = product_code)
            product_id = product.id
            warehouse_list = QuantityByWarehouse.objects.filter(product_id = product_id).values('warehouse_code', 'total_quantity')
            dict_product = {}
            dict_product_id = {product_code : dict_product}
            for warehouse_code in warehouse_list:
                code = warehouse_code['warehouse_code']
                total_quantity = warehouse_code['total_quantity']
                dict_product[code] = total_quantity   
            
            list_A.append(dict_product_id)

        return JsonResponse({'message' : list_A})

class SheetListView(View):
    def get(self, request):
        type = request.GET.get('type', None)

        q = Q()
        if type:
            q &= Q(type__icontains = type)

        
        sheets = Sheet.objects.filter(q).values(
            'id',
            'user',
            'type',
            'company_code',
            'etc',
            'created_at'
        ).order_by('created_at')

        for_list = []
        for sheet in sheets:
            id           = sheet['id']
            user_name    = User.objects.get(id = sheet['user']).name
            type         = sheet['type']
            # type 체인지
            if type == 'inbound':
                type = '입고'
            elif type == 'outbound':
                type = '출고'
            elif type == 'generate':
                type = '세트 생산'
            elif type == 'used':
                type = '소모'

            company_name = Company.objects.get(code = sheet['company_code']).name
            etc          = sheet['etc']
            created_at   = sheet['created_at']
            
            dict = {
                'id'        :  id,       
                'type'      : type,
                'user'      : user_name,
                'created_at'    : created_at,
                'company_name'  : company_name,
                'etc'       : etc
            }
            
            for_list.append(dict)


        return JsonResponse({'message' : for_list}, status = 200)

class InfoSheetListView(View):
    def get(self, request):
        type = request.GET.get('type', None)
        name = request.GET.get('user_name', None)
        company_name = request.GET.get('company_name', None)
        date_start = request.GET.get('date_start', None)
        date_end   = request.GET.get('date_end')
        warehouse_code = request.GET.get('warehouse_code', None)
        product_code = request.GET.get('product_code')

        if not date_start:
            return JsonResponse({'message' : "기준 시작 날짜 설정 오류"}, status = 403)
        if not date_end:
            return JsonResponse({'message' : "기준 종료 날짜 설정 오류"}, status = 403)

        q = Q(created_at__range = (date_start, date_end))

        if type:
            q &= Q(type__icontains = type)
        if name:
            user_id = User.objects.get(name = name).id
            q &= Q(user__icontains = user_id)
        if company_name:
            company_code = Company.objects.get(name = company_name).code
            q &= Q(company_code__icotains = company_code)
            


        
        sheet_ids = Sheet.objects.filter(q).values_list('id', flat= True).order_by('created_at')

        

        for_list = []
        for sheet_id in sheet_ids:
            sheet = Sheet.objects.get(id = sheet_id)
            id           = sheet.id
            user_name    = User.objects.get(id = sheet.user.id).name
            type         = sheet.type
            # type 체인지
            if type == 'inbound':
                type = '입고'
            elif type == 'outbound':
                type = '출고'
            elif type == 'generate':
                type = '세트 생산'
            elif type == 'used':
                type = '소모'

            company_name = Company.objects.get(code = sheet.company_code).name
            etc          = sheet.etc
            created_at   = sheet.created_at
            
            q2 = Q()

            if warehouse_code:
                q &= Q(warehouse_code__icontains = warehouse_code)
            if product_code:
                product_id = Product.objects.get(product_code = product_code).id
                q &= Q(product_code__exact = product_id)


            compositions = SheetComposition.objects.filter(q2)
            for composition in compositions:
                product = Product.objects.get(id = composition.product_id)
                
                total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))

                serial_codes = SerialInSheetComposition.objects.filter(sheet_composition = composition).values('serial_code')

                list_serial_code = []
            
                for object in serial_codes:
                    list_serial_code.append(object.get('serial_code'))

                if product.company_code == "" :
                    dict = {
                        'sheet_id'              : id,
                        'user_name'             : user_name,
                        'type'                  : type,
                        'company_name'          : company_name,
                        'etc'                   : etc,
                        'created_at'            : created_at,
                        'product_code'          : product.product_code,
                        'product_name'          : product.name,
                        'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                        'barcode'               : product.barcode,
                        'unit_price'            : composition.unit_price,
                        'quantity'              : composition.quantity,
                        'total_quantity'        : total['total_quantity__sum'],
                        'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                        'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                        'location'              : composition.location,
                        'serial_codes'          : list_serial_code,
                        'etc'                   : composition.etc   
                    } 
                else:
                    dict = {
                        'sheet_id'              : id,
                        'user_name'             : user_name,
                        'type'                  : type,
                        'company_name'          : company_name,
                        'etc'                   : etc,
                        'created_at'            : created_at,
                        'product_code'          : product.product_code,
                        'product_name'          : product.name,
                        'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                        'barcode'               : product.barcode,
                        'company_name'          : Company.objects.get(code = product.company_code).name,
                        'unit_price'            : composition.unit_price,
                        'quantity'              : composition.quantity,
                        'total_quantity'        : total['total_quantity__sum'],
                        'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                        'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                        'location'              : composition.location,
                        'serial_codes'          : list_serial_code,
                        'etc'                   : composition.etc   
                    }

            for_list.append(dict)


        return JsonResponse({'message' : for_list}, status = 200)

class ClickSheetView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id', None)

        if not sheet_id:
            return JsonResponse({'message' : 'sheet id 가 입력되지 않았습니다.'}, status = 200)

        compositions = SheetComposition.objects.filter(sheet_id = sheet_id).prefetch_related('serialinsheetcomposition_set')

        for_list = []
        for composition in compositions:
            product = Product.objects.get(id = composition.product_id)
            total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))

            serial_codes = SerialInSheetComposition.objects.filter(sheet_composition = composition).values('serial_code')

            list_serial_code = []
            
            for object in serial_codes:
                list_serial_code.append(object.get('serial_code'))

            if product.company_code == "" :
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'barcode'               : product.barcode,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list_serial_code,
                    'etc'                   : composition.etc   
                } 
            else:
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'barcode'               : product.barcode,
                    'company_name'          : Company.objects.get(code = product.company_code).name,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list_serial_code,
                    'etc'                   : composition.etc   
                }

            for_list.append(dict)

        return JsonResponse({'message' : for_list}, status = 200)
    
class TotalQuantityView(View):
    def get(self, request):
        warehouse_code = request.GET.get('warehouse_code', None)

        result_list = []

        if warehouse_code:
            check = QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code)

            for obj in check:
                get_product = Product.objects.get(id = obj.product_id)
                dict = {
                    'product_code' : get_product.product_code,
                    'product_name' : get_product.name,
                    'warehouse_code' : obj.warehouse_code,
                    'warehouse_name' : Warehouse.objects.get(code = obj.warehouse_code).name,
                    'status'       : get_product.status,
                    'safe_quantity': get_product.safe_quantity,
                    'quantity'     : obj.total_quantity,
                    'ketword'      : get_product.keyword
                }
                result_list.append(dict) 
            return JsonResponse({'message': result_list})
        
        else:
            ids = []
            
            for product_id in QuantityByWarehouse.objects.all().values('product'):
                ids.append(product_id['product'])

            for num in set(ids):
                get_product = Product.objects.get(id = num)
                check = QuantityByWarehouse.objects.filter(product_id = num).aggregate(quantity = Sum('total_quantity'))
                dict = {
                    'product_code' : get_product.product_code,
                    'product_name' : get_product.name,
                    'status'       : get_product.status,
                    'safe_quantity': get_product.safe_quantity,
                    'quantity'     : check['quantity'],
                    'ketword'      : get_product.keyword
                }
                result_list.append(dict) 
            return JsonResponse({'message': result_list})

class PriceCheckView(View):
    def post(self, request):
        input_data = request.POST
        
        try:
            company_code = input_data['company_code']
            product_id   = Product.objects.get(product_code = input_data['product_code']).id
            print(product_id)
            type         = input_data['type']
            
            if type == 'inbound':
                price = ProductPrice.objects.get(company_code = company_code, product_id = product_id).inbound_price
            
            if type == 'outbound':
                price = ProductPrice.objects.get(company_code = company_code, product_id = product_id).outbound_price
        
            return JsonResponse({'message' : f'{price}'}, status = 200)
        
        
        except Product.DoesNotExist:    
            return JsonResponse({'message' : '잘못된 요청을 보내셨습니다.2'}, status = 403)
        except ProductPrice.DoesNotExist:
            return JsonResponse({'message' : '0' }, status = 200)
        
class SerialCodeCheckView(View):
    def serial_product_code_checker(self, serial_code):
        product_id = SerialAction.objects.get(serial = serial_code).product.id

        product_code = Product.objects.get(id = product_id).product_code
        return product_code

    def serial_tracker(self, serial_code):
        serial_actions = SerialAction.objects.get(serial = serial_code).actions
        sheets = serial_actions.split(',')
        
        last_sheet = max(sheets)

        sheet = Sheet.objects.get(id = last_sheet)

        return sheet

    def print_sheet(self, sheet):
        sheet_compositions = SheetComposition.objects.filter(sheet_id = sheet.id)
        
        products = []
        
        for composition in sheet_compositions:
            product = Product.objects.get(id = composition.product_id)
            total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))

            serial_codes = SerialInSheetComposition.objects.filter(sheet_composition = composition).values('serial_code')

            list_serial_code = []
            
            for object in serial_codes:
                list_serial_code.append(object.get('serial_code'))

            if product.company_code == "" :
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'barcode'               : product.barcode,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list_serial_code,
                    'etc'                   : composition.etc   
                } 
            else:
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'barcode'               : product.barcode,
                    'company_name'          : Company.objects.get(code = product.company_code).name,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list_serial_code,
                    'etc'                   : composition.etc   
                }

            products.append(dict)
        
        result = {
            'user' : sheet.user.name,
            'type' : sheet.type,
            'company_name' : Company.objects.get(code = sheet.company_code).name,
            'etc'  : sheet.etc,
            # 'created_at'  : sheet.created_at,
            'products'  : [products]
        }
        
        return result

    def get(self, request):
        serial_code  = request.GET.get('serial_code')
        process_type = request.GET.get('process_type')

        
        if process_type == 'inbound':
            if not SerialAction.objects.filter(serial = serial_code).exists():
                return JsonResponse({'message' : '입고 처리가 가능합니다.'}, status = 200)
            
            else:
                sheet = self.serial_tracker(serial_code)
                sheet_type  = sheet.type
                
                if sheet_type == 'inbound':
                    result = self.print_sheet(sheet)
                    return JsonResponse({'message': '보유하고 있는 시리얼 입니다.', 'result': result}, status = 403)

                if sheet_type == 'create':
                    result = self.print_sheet(sheet)
                    return JsonResponse({'message': '보유하고 있는 시리얼 입니다.', 'result': result}, status = 403)
        
                else:
                    return JsonResponse({'message' : '입고 처리가 가능합니다.'}, status = 200)

        if process_type == 'outbound':
            if not SerialAction.objects.filter(serial = serial_code).exists():
                return JsonResponse({'message' : '존재하지 않는 시리얼입니다.'}, status = 403)

            else:
                sheet = self.serial_tracker(serial_code)
                sheet_type  = sheet.type

                if sheet_type == "inbound":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.' , 'product_code' : product_code}, status = 200)

                if sheet_type == "create":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.', 'product_code' : product_code}, status = 200)

                if sheet_type == "outbound":
                    result = self.print_sheet(sheet)
                    return JsonResponse({'message': '이미 출고된 시리얼 입니다.', 'result': result }, status = 403)

class SerialActionHistoryView(View):
    def print_sheet(self, sheets):
        sheet_list = []

        for id in sheets:
            sheet = Sheet.objects.get(id = id)
            dic_sheet = {
                'id'            : sheet.id,
                'user_name'     : sheet.user.name,         
                'type'          : sheet.type,   
                'company_name'  : Company.objects.get(code = sheet.company_code).name,       
                'etc'           : sheet.etc,          
                'created_at'    : sheet.created_at         
            }

            sheet_list.append(dic_sheet)

        return sheet_list

    def get(self, request):
        serial_code = request.GET.get("serial_code", None)

        actions = SerialAction.objects.get(serial = serial_code).actions
        sheets = actions.split(",")
        
        sheet_list = self.print_sheet(sheets)

        return JsonResponse({'message': sheet_list}, status = 200)

class StockTotalView(View):
    def get(self, request):
        product_name    = request.GET.get('product_name', None)
        product_code    = request.GET.get('product_code', None)
        keyword         = request.GET.get('keyword', None)
        barcode         = request.GET.get('barcode', None)
        
        type            = request.GET.get('type', None)
        company_code    = request.GET.get('company_code', None)

        warehouse_code  = request.GET.get('warehouse_code', None)

        q = Q()
        if product_name:
            q &= Q(name__icontains = product_name)
        if product_code:
            q &= Q(product_code__icontains = product_code)
        if barcode:
            q &= Q(barcode__icontains = barcode)
        if keyword:
            q &= Q(keyword__icontains = keyword)

        target_products = Product.objects.filter(q)

        result = []

        try:
            for product in target_products:
                list_A = QuantityByWarehouse.objects.filter(product_id = product.id)
                
                total_quantity = 0
                for obj in list_A:
                    total_quantity += obj.total_quantity

                price = 0
                if type == 'inbound':
                    if not company_code:
                        price = 0
                    else:
                        check_price = ProductPrice.objects.get(company_code = company_code, product_id = product.id)
                        price = check_price.inbound_price

                if type == 'outbound':
                    if not company_code:
                        price = 0
                    else:
                        check_price = ProductPrice.objects.get(company_code = company_code, product_id = product.id)
                        price = check_price.outbound_price
                
                if not warehouse_code:
                    try:
                        partial_quantity = QuantityByWarehouse.objects.get(product_id = product.id, warehouse_code = product.warehouse_code).total_quantity
                    except QuantityByWarehouse.DoesNotExist:
                        partial_quantity = 0
                    dict = {
                        'product_name'      : product.name,
                        'product_code'      : product.product_code,
                        'warehouse_name'    : Warehouse.objects.get(code =product.warehouse_code).name,
                        'warehouse_code'    : product.warehouse_code,
                        'location'          : product.location,
                        'partial_quantity'  : partial_quantity,
                        'total_quantity'    : total_quantity,
                        'latest_price'      : price,
                        'status'            : product.status
                    }
                else:
                    try:
                        partial_quantity = QuantityByWarehouse.objects.get(product_id = product.id, warehouse_code = product.warehouse_code).total_quantity
                    except QuantityByWarehouse.DoesNotExist:
                        partial_quantity = 0
                    
                    dict = {
                        'product_name'      : product.name,
                        'product_code'      : product.product_code,
                        'warehouse_name'    : Warehouse.objects.get(code = warehouse_code).name,
                        'warehouse_code'    : warehouse_code,
                        'location'          : product.location,
                        'partial_quantity'  : partial_quantity,
                        'total_quantity'    : total_quantity,
                        'latest_price'      : price,
                        'status'            : product.status
                    }
                result.append(dict)
            
            return JsonResponse({'message' : result})
        except Product.DoesNotExist:    
            return JsonResponse({'message' : '잘못된 요청을 보내셨습니다.2'}, status = 403)
        except ProductPrice.DoesNotExist:
            return JsonResponse({'message' : '0' }, status = 403)


#------------------------------------------------------------------------------------#
# class CreateSheetTypeView(View):
#     def post(self, request):
#         name = request.POST['name']

#         SheetType.objects.create(name = name)

#         return JsonResponse({'message' : 'sheet type 생성 성공'}, status = 200)

# class DeleteSheetTypeView(View):
#     def post(self, request):
#         id = request.POST['sheet_type_id']

#         SheetType.objects.delete(id = id)

#         return JsonResponse({'message' : 'sheet type 생성 성공'}, status = 200)
