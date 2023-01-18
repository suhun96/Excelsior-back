import json, re

import datetime

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from django.db.models   import Q , Sum
from datetime           import datetime

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
                if Company.objects.filter(id = input_company).exists() == False:
                    raise Exception({'message' : '존재하지 않는 회사입니다.'})
                
                for product in input_products:
                    product_id = Product.objects.get(product_code =product['product_code']).id
                    ProductPrice.objects.update_or_create(
                        product_id = product_id,
                        company_id = input_company,
                        defaults={
                            'inbound_price' : product['price']
                        }
                    )
                    
            elif input_data['type'] == 'outbound':
                if Company.objects.filter(id = input_company).exists() == False:
                    raise Exception({'message' : '존재하지 않는 회사입니다.'})

                for product in input_products:
                    product_id = Product.objects.get(product_code =product['product_code']).id
                    ProductPrice.objects.update_or_create(
                        product_id = product_id,
                        company_id = input_company,
                        defaults={
                            'outbound_price' : product['price']
                        }
                    )
            
            elif input_data['type'] == 'new':
                pass
            
    except:
        raise Exception({'message' : 'register_checker를 생성하는중 에러가 발생했습니다.'})

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
        if not Company.objects.filter(id = input_company).exists():
            raise Exception('존재하지 않는 회사입니다.')
        with transaction.atomic():
            new_sheet = Sheet.objects.create(
                user_id = input_user,
                type = input_type,
                company_id = input_company,
                date = input_date,
                etc  = input_etc
            )

            generate_document_num(new_sheet.id)

            if not input_products:
                raise Exception('입,출고서에 제품을 비워 등록할 수 없습니다.')
            

            for product in input_products:
                product_code = product['product_code']
                product_id   = Product.objects.get(product_code =product['product_code']).id

                if Product.objects.filter(product_code = product_code).exists() == False:
                    raise Exception(f'{product_code}는 존재하지 않습니다.') 

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
                    if product['serial_code'] == None:
                        pass    
                    else:
                        for serial_code in product['serial_code']:
                            # 입/출고 구성품의 serial_code 연결
                            serial_code_checker(serial_code, input_type)
                            SerialCode.objects.create(
                                sheet_id = new_sheet.id,
                                product_id = product_id,
                                code = serial_code
                            )
        
        return new_sheet
    except:
        raise Exception('sheet를 생성하는중 에러가 발생했습니다.')

def create_product_serial_code(product_id, quantity, new_sheet_id):
    now = datetime.now()
    year    = str(now.year)
    month   = str(now.month).zfill(2)
    day     = str(now.day).zfill(2)
    today = year[2:4] + month + day

    product_code = Product.objects.get(id = product_id).product_code

    serial_code1 = product_code + today

    if not SerialCode.objects.filter(code__icontains = serial_code1).exists():
        for i in range(int(quantity)):
            route = '01'
            numbering = str(i + 1).zfill(3)
            serial_code2 = serial_code1 + route + numbering   
            SerialCode.objects.create(code = serial_code2, sheet_id = new_sheet_id, product_id = product_id)
    else:
        last_serial = SerialCode.objects.filter(code__icontains = serial_code1).latest('id').code
        
        before_route = last_serial.replace(serial_code1, "")
        before_route = before_route[:2]
        
        after_route = int(before_route) + 1
        
        for i  in range(int(quantity)):
            numbering = str(i + 1).zfill(3)
            serial_code2 = serial_code1 + str(after_route).zfill(2) + numbering
            SerialCode.objects.create(code = serial_code2, sheet_id = new_sheet_id, product_id = product_id)

def create_set_serial_code(input_data, generate_sheet_id):
    now = datetime.now()
    year    = str(now.year)
    month   = str(now.month).zfill(2)
    day     = str(now.day).zfill(2)
    today = year[2:4] + month + day

    set_product_code = input_data.get('set_product_code')
    manufacture_quantity = input_data.get('manufacture_quantity')

    product_id      = Product.objects.get(product_code = set_product_code).id
    quantity        = manufacture_quantity
    
    serial_code1 = set_product_code + today

    if not SerialCode.objects.filter(code__icontains = serial_code1).exists():
        route = '01'
        for i  in range(int(manufacture_quantity)):
            numbering = '001'
            serial_code2 = serial_code1 + route + numbering   
            SerialCode.objects.create(code = serial_code2, sheet_id = generate_sheet_id, product_id = product_id)
    else:
        last_serial = SerialCode.objects.filter(code__icontains = serial_code1).latest('id').code
        
        before_route = last_serial.replace(serial_code1, "")
        before_route = before_route[:2]
        
        after_route = int(before_route) + 1
        
        for i  in range(int(manufacture_quantity)):
            numbering = str(i + 1).zfill(3)
            serial_code2 = serial_code1 + str(after_route).zfill(2) + numbering
            SerialCode.objects.create(code = serial_code2, sheet_id = generate_sheet_id, product_id = product_id)

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
                    if product['serial_code'] == None:
                        pass    
                    else:
                        for serial_code in product['serial_code']:
                            # 입/출고 구성품의 serial_code 연결
                            type = Sheet.objects.get(id = sheet_id).type
                            serial_code_checker(serial_code, type)
                            SerialCode.objects.create(
                                sheet_id = sheet_id,
                                product_id = product_id,
                                code = serial_code
                            )
    except:
        raise Exception('create_sheet_detail 사용하는중 에러가 발생했습니다.')

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
                    if product['serial_code'] == None:
                        pass    
                    else:
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
            
            # if target_sheet.type == 'return':
            #     target_details = SheetComposition.objects.filter(sheet_id = sheet_id).values(
            #             'product',
            #             'unit_price',
            #             'quantity',
            #             'warehouse_code'
            #         )

            #     for detail in target_details:
            #         product_id     = detail.get('product')
            #         warehouse_code = detail.get('warehouse_code')
            #         quantity       = detail.get('quantity') 
            #         unit_price     = detail.get('unit_price')
                    
            #         stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                    
            #         # 반품일 경우 (-)
            #         before_quantity = stock.last().stock_quantity
            #         stock_quantity  = before_quantity - int(quantity)
                    
            #         StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
            #             sheet_id = sheet_id,
            #             stock_quantity = stock_quantity,
            #             product_id = product_id,
            #             warehouse_code = warehouse_code )
                    
            #         mam_delete_sheet(product_id, unit_price, quantity, stock_quantity)

            #         QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
            #             product_id = product_id,
            #             warehouse_code = warehouse_code,
            #             defaults={'total_quantity' : stock_quantity})

            if target_sheet.type == 'new':
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
                    
                    # 반품일 경우 (-)
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

            if target_sheet.type == 'used':
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
                    stock_quantity  = before_quantity + int(quantity)
                    
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

            if target_sheet.type == 'generate':
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

                    if Product.objects.get(id = product_id).is_serial == True:
                        create_product_serial_code(product_id, quantity, target_sheet.id)
                    else:
                        pass


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
            custom_price = 0,
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

        try:
            result1 = (mul_stock - mul_inbound) / (total_quantity - quantity)
            round_result = round(result1, 6)
        except ZeroDivisionError
            round_result = 0

        new_MAM = MovingAverageMethod.objects.filter(product_id= product_id).update(
            average_price = round_result,
            total_quantity = stock_quantity
        )

def count_serial_code(input_data, component, used_sheet):
    set_product_code = input_data.get('set_product_code')
    set_product_id = Product.objects.get(product_code = set_product_code).id
    set_components_ids = ProductComposition.objects.filter(set_product_id = set_product_id).values_list('composition_product', flat= True)
    
    serial_list = component.get('serials')
    serial_quantity = len(serial_list)

    try:
        if not serial_quantity == component.get('quantity'):
            raise Exception('시리얼 갯수와 요청하신 수량이 일치하지 않습니다.')

        for serial in serial_list:
            serial_product_id = SerialCode.objects.filter(code = serial).latest('id').product_id
            component_quantity = ProductComposition.objects.get(set_product_id = set_product_id, composition_product_id = serial_product_id).quantity

            if not serial_quantity == component_quantity:
                raise Exception('생산시 요구되는 시리얼 갯수와 입력하신 시리얼 갯수가 일치하지 않습니다.')

            if not serial_product_id in set_components_ids:
                raise Exception('시리얼 코드 불일치를 발견했습니다.')
            
            # 추가 
            sheet_id = SerialCode.objects.filter(code = serial).latest('id').sheet_id

            sheet_type = Sheet.objects.get(id = sheet_id).type
            
            if sheet_type == 'outbound':
                raise Exception('이미 출고된 시리얼 입니다.')
            if sheet_type == 'used':
                raise Exception('이미 사용된 시리얼 입니다.')

            SerialCode.objects.create(
                sheet_id = used_sheet.id,
                product_id = serial_product_id,
                code = serial
            )
    except Exception:
        raise Exception('입력한 시리얼 코드를 체크하는중 오류가 발생했습니다.')
    
def generate_document_num(sheet_id):
    target_sheet = Sheet.objects.get(id = sheet_id)
    stock_type = target_sheet.type
    year  = target_sheet.date.year
    month = str(target_sheet.date.month).zfill(2)
    day   = str(target_sheet.date.day).zfill(2)
    
    
    # 타입 변환기.
    if stock_type == 'inbound':
        stock_type = "입고"
    if stock_type == "outbound":
        stock_type = "출고"
    if stock_type == 'generate':
        stock_type = '생산'
    if stock_type == 'new':
        stock_type = '신규'
    if stock_type == 'used':
        stock_type = '사용'
    if stock_type == 'return':
        stock_type = '반품'

    check_sheet_date = Sheet.objects.filter(date = target_sheet.date)

    if check_sheet_date.exists():
        count_document = check_sheet_date.count()
        num = count_document
        document_num = f"{year}{month}{day}-{stock_type}-{num}"
    else:
        num = 1
        document_num = f"{year}{month}{day}-{stock_type}-{num}"
    
    try:
        with transaction.atomic():
            target_sheet.document_num = document_num
            target_sheet.save()
    except Exception:
        raise ('문서번호 생성중 오류 발생.')        

def modify_sheet_data(sheet_id, modify_user, modify_data):
    UPDATE_SET = {'user' : modify_user}

    update_opt_1 = ['company_id', 'etc', 'date']

    for key, value in modify_data.items():
        if key == 'date':
            generate_document_num(sheet_id)
        if key in update_opt_1:
            UPDATE_SET.update({ key : value })

    Sheet.objects.filter(id = sheet_id).update(**UPDATE_SET)

    tartget_sheet = Sheet.objects.get(id = sheet_id)
    tartget_sheet.updated_at = datetime.now()
    tartget_sheet.save()

def modify_sheet_detail_2(sheet_id, products):
    try:
        for product in products:
            product_code = product['product_code']
            product_id   = Product.objects.get(product_code =product['product_code']).id

            if Product.objects.filter(product_code = product_code).exists() == False:
                raise Exception({'message' : f'{product_code}는 존재하지 않습니다.'}) 

            target_sheet_detail = SheetComposition.objects.get(sheet_id = sheet_id, product_id = product_id)
            
            if 'unit_price' in product:
                target_sheet_detail.unit_price = product['unit_price']
                target_sheet_detail.save()
            if 'etc' in product:
                target_sheet_detail.unit_price = product['etc']
                target_sheet_detail.save()

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
        raise Exception({'message' : 'create_sheet_detail 사용하는중 에러가 발생했습니다.(check-point3)'})

def serial_tracker2(serial_code):
        sheet_id = SerialCode.objects.filter(code = serial_code).latest('id').sheet_id

        sheet = Sheet.objects.get(id = sheet_id )

        return sheet

def serial_code_checker(serial_code, process_type):
    if process_type == 'inbound':
        if not SerialCode.objects.filter(code = serial_code).exists():
            pass
        
        else:
            sheet = serial_tracker2(serial_code)
            sheet_type  = sheet.type
            
            if sheet_type == 'inbound':
                raise Exception('이미 보유하고 있는 시리얼 입니다.')

            if sheet_type == 'generate':
                raise Exception('이미 보유하고 있는 시리얼 입니다.')
    
            else:
                pass

    if process_type == 'outbound':
        if not SerialCode.objects.filter(code = serial_code).exists():
            raise Exception('존재하지 않는 시리얼 코드는 출고 불가능합니다.')

        else:
            sheet = serial_tracker2(serial_code)
            sheet_type  = sheet.type

            if sheet_type == "new":
                pass

            if sheet_type == "inbound":
                pass

            if sheet_type == "generate":
                pass

            if sheet_type == "outbound":
                raise Exception('이미 출고된 시리얼 입니다.')

            if sheet_type == "used":
                raise Exception('세트 생산에 사용된 시리얼 입니다.')