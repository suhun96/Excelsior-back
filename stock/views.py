import json, re

from datetime           import datetime
from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from django.db.models   import Q

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
                product_id      = Product.objects.get(product_code = key).id 
                quantity        = valuse.get('quantity')
                unit_price      = valuse.get('price')
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

        if new_sheet.type == 'generate':
            compositions_1 = SheetComposition.objects.filter(sheet_id = new_sheet_id).values(
                    'product',
                    'unit_price',
                    'quantity',
                    'warehouse_code'
                )

            for composition in compositions_1:
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

                StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                    sheet_id = new_sheet_id,
                    stock_quantity = stock_quantity,
                    defaults={
                        'product_id' : product_id,
                        'warehouse_code' : warehouse_code
                    })
            
            # 여기서부터 소진 sheet

            Set_compositions = ProductComposition.objects.filter(set_product_id = product_id).values('composition_product', 'quantity')

            used_sheet = Sheet.objects.create(
                    user_id = 1,
                    type    = 'used',
                    company_code = 'EX'
                )
            


            for composition_product in Set_compositions:

                SheetComposition.objects.create(
                    sheet_id        = used_sheet.id,
                    product_id      = composition_product['composition_product'],
                    unit_price      = 0,
                    quantity        = composition_product['quantity'], 
                    warehouse_code  = warehouse_code,
                    location        = 0
                )
            
            compositions_2 = SheetComposition.objects.filter(sheet_id = used_sheet.id).values(
                    'product',
                    'unit_price',
                    'quantity',
                    'warehouse_code'
                )
            
            for composition in compositions_2:
                product_id     = composition.get('product')
                warehouse_code = composition.get('warehouse_code')
                quantity       = composition.get('quantity')
                # unit_price     = composition.get('unit_price') 
                
                stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                
                if stock.exists():
                    before_quantity = stock.last().stock_quantity
                    stock_quantity  = before_quantity - int(quantity)
                else:
                    stock_quantity  = quantity

                StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                    sheet_id = used_sheet.id,
                    stock_quantity = stock_quantity,
                    defaults={
                        'product_id' : product_id,
                        'warehouse_code' : warehouse_code
                    })

            return JsonResponse({'message' : '생산 성공'}, status = 200)


class QunatityByWarehouseView(View):
    def get(self, request):
        
        product_id_list = request.GET.getlist('product_id', None)
        
        list_A = []
        for product_id in product_id_list:
            warehouse_list = QuantityByWarehouse.objects.filter(product_id = product_id).values('warehouse_code', 'total_quantity')
            dict_product = {}
            dict_product_id = {product_id : dict_product}
            for warehouse_code in warehouse_list:
                code = warehouse_code['warehouse_code']
                total_quantity = warehouse_code['total_quantity']
                dict_product[code] = total_quantity   
            
            list_A.append(dict_product_id)

        return JsonResponse({'message' : list_A})