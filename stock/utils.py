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
        input_company = input_data.get('company_id')

        try:
            with transaction.atomic():
                if input_data['type'] == 'inbound':
                    for product in input_products:
                        product_id = Product.objects.get(product_code =product['product_code']).id
                        ProductPrice.objects.update_or_create(
                            product_id = product_id,
                            company_id = input_company,
                            defaults={
                                'inbound_price' : product['price']
                            }
                        )
                        
                if input_data['type'] == 'outbound':
                    for product in input_products:
                        product_id = Product.objects.get(product_code =product['product_code']).id
                        ProductPrice.objects.update_or_create(
                            product_id = product_id,
                            company_id = input_company,
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
        input_date = input_data.get('date', None)
        input_etc  = input_data.get('etc', None)
        input_company = input_data.get('company_id', None)
        input_products = input_data.get('products', None)
        
        try:
            with transaction.atomic():
                new_sheet = Sheet.objects.create(
                    user_id = input_user,
                    type = input_type,
                    company_id = input_company,
                    date = input_date,
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
                        etc             = product['etc']
                    )

                    if 'serial_code' in product:
                        for serial_code in product['serial_code']:
                            # 입/출고 구성품의 serial_code 연결
                            SerialCode.objects.create(
                                sheet_id = new_sheet.id,
                                product_id = product_id,
                                code = serial_code
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

        if not SerialCode.objects.filter(code__icontains = serial_code1).exists():
            for i in range(quantity):
                route = '01'
                numbering = str(i + 1).zfill(3)
                serial_code2 = serial_code1 + route + numbering   
                SerialCode.objects.create(code = serial_code2, sheet_id = new_sheet_id, product_id = product_id)
        else:
            last_serial = SerialCode.objects.filter(code__icontains = serial_code1).latest('id').code
            
            before_route = last_serial.replace(serial_code1, "")
            before_route = before_route[:2]
            
            after_route = int(before_route) + 1
            
            for i  in range(quantity):
                numbering = str(i + 1).zfill(3)
                serial_code2 = serial_code1 + str(after_route).zfill(2) + numbering
                SerialCode.objects.create(code = serial_code2, sheet_id = new_sheet_id, product_id = product_id)

def create_sheet_logs(sheet_id, modify_user):
        target_sheet = Sheet.objects.get(id = sheet_id)
        try:
            with transaction.atomic():
                new_sheet_log = SheetLog.objects.create(
                    sheet_id  = target_sheet.id,
                    user_name = modify_user.name,
                    type      = target_sheet.type,
                    company_id = target_sheet.company_id,
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
                    etc             = product['etc']
                )
                if 'serial_code' in product:
                    for serial_code in product['serial_code']:
                        # 입/출고 구성품의 serial_code 연결
                        SerialCode.objects.create(
                            sheet_id = sheet_id,
                            product_id = product_id,
                            code = serial_code
                        )
        except:
            raise Exception({'message' : 'create_sheet_detail 사용하는중 에러가 발생했습니다.'})

def modify_sheet_detail(sheet_id, products):
    try:
        for product in products:
            product_code = product['product_code']
            product_id   = Product.objects.get(product_code =product['product_code']).id

            if Product.objects.filter(product_code = product_code).exists() == False:
                raise Exception({'message' : f'{product_code}는 존재하지 않습니다.'}) 

            modify_sheet_composition = SheetComposition.objects.create(
                sheet_id        = sheet_id,
                product_id      = product_id,
                quantity        = product['quantity'], 
                warehouse_code  = product['warehouse_code'],
                location        = product['location'],
                unit_price      = product['price'],
                etc             = product['etc']
            )
            
            if "modified" in product:
                SerialCode.objects.filter(product_id = product_id, sheet_id = sheet_id).delete()
                if 'serial_code' in product:
                    for serial_code in product['serial_code']:
                        # 입/출고 구성품의 serial_code 연결
                        SerialCode.objects.create(
                            sheet_id = sheet_id,
                            product_id = product_id,
                            code = serial_code
                        )
    except:
        raise Exception({'message' : 'create_sheet_detail 사용하는중 에러가 발생했습니다.2'})

def rollback_sheet_detail(sheet_id):
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
                        unit_price     = detail.get('unit_price')
                        
                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        # 입고일 경우 (-)
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity - int(quantity)
                        
                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        mam_delete_sheet(product_id, unit_price, quantity, stock_quantity)

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
                        unit_price     = composition.get('unit_price')
                        
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

def reflecte_sheet_detail(sheet_id):
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
                        unit_price     = composition.get('unit_price') 
                        
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
                        
                        mam_create_sheet(product_id, unit_price, quantity, stock_quantity)
                        
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
                        unit_price     = composition.get('unit_price')
                        
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

def mam_create_sheet(product_id, unit_price, quantity, stock_quantity):
    try:
        total = QuantityByWarehouse.objects.filter(product_id = product_id).aggregate(Sum('total_quantity'))
        total_quantity = total['total_quantity__sum']      

    except QuantityByWarehouse.DoesNotExist:
        total_quantity = quantity
        
    if not MovingAverageMethod.objects.filter(product_id = product_id).exists():
        new_MAM = MovingAverageMethod.objects.create(
            product_id = product_id,
            average_price = unit_price,
            total_quantity = total_quantity
        )
    else:
        average_price = MovingAverageMethod.objects.get(product_id = product_id).average_price
        mul_stock   = average_price * total_quantity
        mul_inbound = unit_price * quantity

        result1 = (mul_stock + mul_inbound) / (total_quantity + quantity)
        round_result = round(result1, 6)
        
        new_MAM = MovingAverageMethod.objects.filter(product_id= product_id).update(
            average_price = round_result,
            total_quantity = stock_quantity
        )

def mam_delete_sheet(product_id, unit_price, quantity, stock_quantity):
    try:
        total = QuantityByWarehouse.objects.filter(product_id = product_id).aggregate(Sum('total_quantity'))
        total_quantity = total['total_quantity__sum']      

    except QuantityByWarehouse.DoesNotExist:
        total_quantity = unit_price

    if not MovingAverageMethod.objects.filter(product_id = product_id).exists():
        new_MAM = MovingAverageMethod.objects.create(
            product_id = product_id,
            average_price = unit_price,
            total_quantity = total_quantity
        )
    else:
        average_price = MovingAverageMethod.objects.get(product_id = product_id).average_price
        mul_stock   = average_price * total_quantity
        mul_inbound = unit_price * quantity

        
        result1 = (mul_stock - mul_inbound) / (total_quantity - quantity)
        round_result = round(result1, 6)

        new_MAM = MovingAverageMethod.objects.filter(product_id= product_id).update(
            average_price = round_result,
            total_quantity = stock_quantity
        )