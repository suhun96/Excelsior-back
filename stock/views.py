import json, re

from datetime           import datetime
from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction

# Models
from stock.models       import *
from products.models    import *
from users.models       import *
from locations.models   import *


# deco
from users.decorator    import jwt_decoder

class CreateSheetView(View):
    def create_sheet(self, input_data):
        input_data = input_data

        #
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
                    }
                    )
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

                StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                    sheet_id = new_sheet_id,
                    stock_quantity = stock_quantity,
                    defaults={
                        'product_id' : product_id,
                        'warehouse_code' : warehouse_code
                    })
                
            return JsonResponse({'message' : '출고 성공'}, status = 200)

        