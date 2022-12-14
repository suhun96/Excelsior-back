import json, re

from datetime           import datetime
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

                    if Product.objects.filter(product_code = product_code).exists() == False:
                        raise Exception({'message' : f'{product_code}는 존재하지 않습니다.'}) 
                        
                    quantity        = product['quantity']
                    warehouse_code  = product['warehouse_code']
                    product_id      = Product.objects.get(product_code =product['product_code']).id
                    unit_price      = product['price']
                    location        = product['location']

                    new_sheet_composition = SheetComposition.objects.create(
                        sheet_id        = new_sheet.id,
                        product_id      = product_id,
                        quantity        = quantity, 
                        warehouse_code  = warehouse_code,
                        location        = location,
                        unit_price      = unit_price,
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
                        # unit_price     = composition.get('unit_price') 
                        
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
                    telegram_bot()

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
                        # unit_price     = composition.get('unit_price') 
                        
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
                    telegram_bot()
                    
                    return JsonResponse({'message' : '출고 성공'}, status = 200)

                if new_sheet.type == 'generate':
                    generated_composition = SheetComposition.objects.get(sheet_id = new_sheet_id)

                    product_id     = generated_composition.product.id
                    warehouse_code = generated_composition.warehouse_code
                    quantity       = generated_composition.quantity
                    # unit_price     = composition.get('unit_price') 


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

class ClickSheetView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id', None)

        if not sheet_id:
            return JsonResponse({'message' : 'sheet id 가 입력되지 않았습니다.'}, status = 200)

        compositions = SheetComposition.objects.filter(sheet_id = sheet_id).values()

        for_list = []
        for composition in compositions:
            product = Product.objects.get(id = composition['product_id'])
            total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))

            if product.company_code == "" :
                dict = {
                    'product_code'          : product.product_code,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'unit_price'            : composition['unit_price'],
                    'quantity'              : composition['quantity'],
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_name'        : Warehouse.objects.get(code = composition['warehouse_code']).name,
                    'stock_quantity'        : QuantityByWarehouse.objects.get(warehouse_code = composition['warehouse_code'], product_id = product.id).total_quantity,
                    'stock_location'        : composition['location'],
                    'etc'                   : composition['etc']   
                } 
            else:
                dict = {
                    'product_code'          : product.product_code,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'company_name'          : Company.objects.get(code = product.company_code).name,
                    'unit_price'            : composition['unit_price'],
                    'quantity'              : composition['quantity'],
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_name'        : Warehouse.objects.get(code = composition['warehouse_code']).name,
                    'stock_quantity'        : QuantityByWarehouse.objects.get(warehouse_code = composition['warehouse_code'], product_id = product.id).total_quantity,
                    'stock_location'        : composition['location'],
                    'etc'                   : composition['etc']   
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
