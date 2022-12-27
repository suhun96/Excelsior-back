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


def register_checker(input_data):
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

def create_sheet(input_data, user):
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

def create_serial_code(composition, new_sheet_id):
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

def create_insert_sheet(input_data, user):
        user = user
        input_data = input_data
        
        input_user      = user.id
        input_type      = input_data.get('type', None)
        input_etc       = input_data.get('etc', None)
        input_company   = input_data.get('company_code', None)
        input_products  = input_data.get('products', None)
        input_date      = input_data.get('date', None)
        
        try:
            with transaction.atomic():
                insert_sheet = Sheet.objects.create(
                    user_id = input_user,
                    type = input_type,
                    company_code = input_company,
                    etc  = input_etc,
                    created_at = input_date
                )

                if not input_products:
                    raise Exception({'message' : '입,출고서에 제품을 비워 등록할 수 없습니다.'})
                

                for product in input_products:
                    product_code = product['product_code']
                    product_id   = Product.objects.get(product_code =product['product_code']).id

                    if Product.objects.filter(product_code = product_code).exists() == False:
                        raise Exception({'message' : f'{product_code}는 존재하지 않습니다.'}) 

                    insert_sheet_composition = SheetComposition.objects.create(
                        sheet_id        = insert_sheet.id,
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
                                sheet_composition = insert_sheet_composition,
                                serial_code = serial_code
                            )
                            
                            # serial 추적
                            if SerialAction.objects.filter(serial = serial_code).exists():
                                # 12월 23일 중단점
                                # if SerialAction.objects.filter(serial_code).count() > 1:
                                    # raise Exception({'messgae' : f'{product_code}는 존재하지 않습니다.'})    
                                
                                actions = SerialAction.objects.get(serial = serial_code).actions
                                actions = actions + f',{insert_sheet.id}'
                                Update_serial_action = SerialAction.objects.filter(serial = serial_code).update(actions = actions)
                            
                            else:
                                SerialAction.objects.create(
                                    serial = serial_code,
                                    product_id = product_id,
                                    actions = insert_sheet.id
                                )

            return insert_sheet
        except:
            raise Exception({'message' : 'sheet를 생성하는중 에러가 발생했습니다.'})

def create_sheet_logs(sheet_id, modify_user):
        target_sheet = Sheet.objects.get(id = sheet_id)
        try:
            with transaction.atomic():
                new_sheet_log = SheetLog.objects.create(
                    sheet_id  = target_sheet.id,
                    user_name = modify_user.name,
                    type      = target_sheet.type,
                    company_code = target_sheet.company_code,
                    etc       = target_sheet.etc,
                )

                target_sheet_details = SheetComposition.objects.filter(sheet_id = target_sheet.id)

                for detail in target_sheet_details:
                    new_sheet_detail_log = SheetCompositionLog.objects.create(
                        sheet_log_id  = new_sheet_log.id,
                        product_id = detail.product.id,
                        unit_price = detail.unit_price,
                        quantity   = detail.quantity,
                        warehouse_code = detail.warehouse_code,
                        location   = detail.location,
                        etc        = detail.etc
                    )
        except:
            raise Exception({'message' : 'create_sheet_logs 사용하는중 에러가 발생했습니다.'})

def create_sheet_detail(sheet_id, products):
        try:
            for product in products:
                product_code = product['product_code']
                product_id   = Product.objects.get(product_code =product['product_code']).id

                if Product.objects.filter(product_code = product_code).exists() == False:
                    raise Exception({'message' : f'{product_code}는 존재하지 않습니다.'}) 

                new_sheet_composition = SheetComposition.objects.create(
                    sheet_id        = sheet_id,
                    product_id      = product_id,
                    quantity        = product['quantity'], 
                    warehouse_code  = product['warehouse_code'],
                    location        = product['location'],
                    unit_price      = product['price'],
                )
        except:
            raise Exception({'message' : 'create_sheet_detail 사용하는중 에러가 발생했습니다.'})

def rollback_quantity(sheet_id):
        target_sheet = Sheet.objects.get(id = sheet_id)
    
        try:
            with transaction.atomic():
                if target_sheet.type == 'inbound':
                    target_details = SheetComposition.objects.filter(sheet_id = sheet_id).values(
                            'product',
                            'unit_price',
                            'quantity',
                            'warehouse_code'
                        )

                    for detail in target_details:
                        product_id     = detail.get('product')
                        warehouse_code = detail.get('warehouse_code')
                        quantity       = detail.get('quantity') 
                        
                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        # 입고일 경우 (-)
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity - int(quantity)
                        
                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})

                if target_sheet.type == 'outbound':
                    compositions = SheetComposition.objects.filter(sheet_id = sheet_id).values(
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

                        # 출고일 경우 (+)       
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity + int(quantity)
                        

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})
        except:
            raise Exception({'message' : 'rollback_quantity 사용하는중 에러가 발생했습니다.'})

def reflecte_modify_sheet_detail(sheet_id):
        target_sheet = Sheet.objects.get(id = sheet_id)
        try:
            with transaction.atomic():
                if target_sheet.type == 'inbound':
                    compositions = SheetComposition.objects.filter(sheet_id = sheet_id).values(
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
                            sheet_id = sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})

                if target_sheet.type == 'outbound':
                    compositions = SheetComposition.objects.filter(sheet_id = sheet_id).values(
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
                            sheet_id = sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})
        except:
            raise Exception({'message' : 'reflecte_modify_sheet_detail 사용하는중 에러가 발생했습니다.'})