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