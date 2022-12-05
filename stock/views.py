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

class NomalStockView(View):
    def create_sheet(self, input_data):
        input_data = input_data

        input_user =  1
        input_type = input_data.get('type', None)
        input_etc  = input_data.get('etc', None)
        input_company = input_data.get('company_code', None)

        new_sheet = Sheet.objects.create(
            user_id = input_user,
            type = input_type,
            company_code = input_company,
            etc  = input_etc
        )
        
        for key, valuse in input_data.items():
            if Product.objects.filter(product_code = key).exists() == True:
                quantity        = valuse.get('quantity')
                unit_price      = valuse.get('price')
                product_id      = Product.objects.get(product_code = key).id 
                location        = valuse.get('location')
                warehouse_code  = valuse.get('warehouse_code')
                
                new_sheet_composition = SheetComposition.objects.create(
                    sheet_id        = new_sheet.id,
                    product_id      = product_id,
                    unit_price      = unit_price,
                    quantity        = quantity, 
                    warehouse_code  = warehouse_code,
                    location        = location
                )
        
        return new_sheet

    def create_serial_code(self, composition, new_sheet_id):
        now = datetime.now()
        year    = str(now.year)
        month   = str(now.month).zfill(2)
        day     = str(now.day).zfill(2)
        today = year[2:4] + month + day

        product_id = composition.get('product')
        quantity       = composition.get('quantity')

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

    def post(self, request):
        input_data = json.loads(request.body)

        new_sheet = self.create_sheet(input_data)
        new_sheet_id = new_sheet.id

        if new_sheet.type == 'inbound':
            compositions = SheetComposition.objects.filter(sheet_id = new_sheet_id).values(
                    'product',
                    'unit_price',
                    'quantity',
                    'warehouse_code'
                )

            for composition in compositions:
                product_id     = composition.get('product')
                print(product_id)
                warehouse_code = composition.get('warehouse_code')
                print(warehouse_code)
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
                
            return JsonResponse({'message' : '출고 성공'}, status = 200)

            

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
                'ID'      :  id,       
                '타입'      : type,
                '작성자'    : user_name,
                '회사명'    : company_name,
                '비고란'    : etc,
                '작성일'    : created_at
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
    
 