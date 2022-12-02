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

class CreateInventorySheetView(View):    
    def post(self, request):
        input_data = request.POST
        product_id      = input_data.get('product_id', None)
        is_inbound      = input_data.get('is_inbound', None)
        company_code    = input_data.get('company_code', None)
        warehouse_code  = input_data.get('warehouse_code', None)
        quantity        = input_data.get('quantity', None)
        unit_price      = input_data.get('unit_price', None)
        etc             = input_data.get('etc', None)
        user_id         = 1
        date            = input_data.get('date', None)
        
        
        if not Product.objects.filter(id = product_id).exists():
            return JsonResponse({'message' : '존재하지 않는 product id 입니다.'}, status = 403)

        if not company_code:
            return JsonResponse({'message' : '거래처가 입력되지 않았습니다.'}, status = 403)
        
        if not Company.objects.filter(code = company_code).exists():
            return JsonResponse({'message' : '거래처 코드가 존재하지 않습니다.'}, status = 403)

        if not warehouse_code: 
            return JsonResponse({'message' : '창고 코드가 입력되지 않았습니다.'}, status = 403)

        if not Warehouse.objects.filter(code = warehouse_code).exists():
            return JsonResponse({'message' : '창고 코드가 존재하지 않습니다'}, status = 403)

        if not quantity:
            return JsonResponse({'message' : '수량이 입력되지 않았습니다.'}, status = 403)

        if not unit_price:
            return JsonResponse({'message' : '입고 가격이 입력되지 않았습니다.'}, status = 403)

        if not is_inbound:
            return JsonResponse({'message' : '입고 형태가 입력되지 않았습니다.'}, status = 403 )

        if not etc:
            etc = ''
        
        if date == None:
            now = datetime.now()
            year    = str(now.year)
            month   = str(now.month).zfill(2)
            day     = str(now.day).zfill(2)
            today = year + month + day
            form_today = datetime.today().strftime('%Y-%m-%d')
        
            if InventorySheet.objects.filter(date = form_today).exists():
                count_num = InventorySheet.objects.filter(date = form_today).count()
                count_num = str(int(count_num) + 1).zfill(4)
            else:
                count_num = '0001'

            doc_no = today + count_num
        
        inventory = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code)
        
        try:
            with transaction.atomic():
                if is_inbound == 'True': # 입고 상태

                    if inventory.exists(): # 창고에 제품이 있는지 조회 '있으면'
                        before_quantity = InventorySheet.objects.select_for_update(nowait= True).filter(product_id = product_id, warehouse_code = warehouse_code, doc_no__lt = doc_no).last().after_quantity
                        after_quantity = int(before_quantity) + int(quantity)
                        
                    else: # 창조에 제품을 조회해 '없으면'
                        before_quantity = 0
                        after_quantity = int(before_quantity) + int(quantity)


                    InventorySheet.objects.create(
                        doc_no          = doc_no,
                        date            = form_today,
                        user_id         = user_id,
                        is_inbound      = is_inbound,
                        product_id      = product_id,
                        company_code    = company_code,
                        warehouse_code  = warehouse_code,
                        unit_price      = unit_price,
                        before_quantity = before_quantity,
                        after_quantity  = after_quantity,
                        quantity        = quantity,
                        etc             = etc
                    )
                
                    return JsonResponse({'message' : '입고 처리가 완료되었습니다.'}, status = 200)

                if is_inbound == 'False': # 출고 재품
                    if inventory.exists(): # 창고에 제품이 있는지 조회 '있으면'
                        before_quantity = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code, doc_no__lt = doc_no).last().after_quantity
                        after_quantity = int(before_quantity) - int(quantity)
                        
                    else: # 창조에 제품을 조회해 '없으면'
                        before_quantity = 0
                        after_quantity = int(before_quantity) - int(quantity)

                    doc_no = self.document_number_generator(date)

                    InventorySheet.objects.create(
                        doc_no          = doc_no,
                        date            = form_today,
                        user_id         = user_id,
                        is_inbound      = is_inbound,
                        product_id      = product_id,
                        company_code    = company_code,
                        warehouse_code  = warehouse_code,
                        unit_price      = unit_price,
                        before_quantity = before_quantity,
                        after_quantity  = after_quantity,
                        quantity        = quantity,
                        etc             = etc
                    )
                    
                    return JsonResponse({'message' : '출고 처리가 완료되었습니다.'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KeyError 가 발생했습니다.'}, status = 403)          

class InsertInventorySheetView(View):
    def post(self, request):
        insert_data = request.POST
        product_id      = insert_data.get('product_id', None)
        is_inbound      = insert_data.get('is_inbound', None)
        company_code    = insert_data.get('company_code', None)
        warehouse_code  = insert_data.get('warehouse_code', None)
        quantity        = insert_data.get('quantity', None)
        unit_price      = insert_data.get('unit_price', None)
        etc             = insert_data.get('etc', None)
        user_id         = 1
        date            = insert_data.get('date', None)

        if not date:
            return JsonResponse({'message' : '삽입할 sheet의 기준일이 입력되지 않았습니다.'}, status = 403)
        
        if not Product.objects.filter(id = product_id).exists():
            return JsonResponse({'message' : '존재하지 않는 product id 입니다.'}, status = 403)

        if not company_code:
            return JsonResponse({'message' : '거래처가 입력되지 않았습니다.'}, status = 403)
        
        if not Company.objects.filter(code = company_code).exists():
            return JsonResponse({'message' : '거래처 코드가 존재하지 않습니다.'}, status = 403)

        if not warehouse_code: 
            return JsonResponse({'message' : '창고 코드가 입력되지 않았습니다.'}, status = 403)

        if not Warehouse.objects.filter(code = warehouse_code).exists():
            return JsonResponse({'message' : '창고 코드가 존재하지 않습니다'}, status = 403)

        if not quantity:
            return JsonResponse({'message' : '수량이 입력되지 않았습니다.'}, status = 403)

        if not unit_price:
            return JsonResponse({'message' : '입고 가격이 입력되지 않았습니다.'}, status = 403)

        if not is_inbound:
            return JsonResponse({'message' : '입고 형태가 입력되지 않았습니다.'}, status = 403 )
        
        if not date:
            return JsonResponse({'message' : 'sheet가 삽입될 날짜가 입력되지 않았습니다.'}, status = 403 )

        if not etc:
            etc = ''


        if InventorySheet.objects.filter(date = date).exists():
                count_num = InventorySheet.objects.filter(date = date).count()
                count_num = str(int(count_num) + 1).zfill(4)
        else:
            count_num = '0001'

        date1 = date.replace('-', '')
        doc_no = date1 + count_num
        
        inventory = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code)
        
        try:
            with transaction.atomic():
                if is_inbound == 'True': # 입고 상태

                    if inventory.exists(): # 창고에 제품이 있는지 조회 '있으면'
                        before_quantity = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code, doc_no__lt = doc_no).last().after_quantity
                        after_quantity = int(before_quantity) + int(quantity)
                        
                    else: # 창조에 제품을 조회해 '없으면'
                        before_quantity = 0
                        after_quantity = int(before_quantity) + int(quantity)


                    InventorySheet.objects.create(
                        doc_no          = doc_no,
                        date            = date,
                        user_id         = user_id,
                        is_inbound      = is_inbound,
                        product_id      = product_id,
                        company_code    = company_code,
                        warehouse_code  = warehouse_code,
                        unit_price      = unit_price,
                        before_quantity = before_quantity,
                        after_quantity  = after_quantity,
                        quantity        = quantity,
                        etc             = etc
                    )

                    UPDATE_LIST = InventorySheet.objects.select_for_update(nowait= True).filter(product_id = product_id, warehouse_code = warehouse_code, doc_no__gt = doc_no).order_by('doc_no').values('doc_no')
            
                    UPDATED_LIST = []
                    # step 4 : 
                    for obj in UPDATE_LIST:
                        update_doc_no = obj.get('doc_no') 
                        UPDATED_LIST.append(update_doc_no)
            
                        before_doc_no = InventorySheet.objects.filter(doc_no__lt = update_doc_no).order_by('-doc_no').first().doc_no

                        before_query = InventorySheet.objects.get(doc_no = before_doc_no)
                        target_query = InventorySheet.objects.get(doc_no = update_doc_no)
                        
                        befoer_query_after_quantity = before_query.after_quantity
                        quantity =  target_query.quantity

                        if target_query.is_inbound == 'True': # 입고면 +, 출고면 -
                            target_query_after_quantity = befoer_query_after_quantity + quantity
                        else:
                            target_query_after_quantity = befoer_query_after_quantity - quantity
                        
                        InventorySheet.objects.filter(doc_no = update_doc_no).update(
                            before_quantity = befoer_query_after_quantity,
                            after_quantity = target_query_after_quantity, 
                            quantity = quantity
                        )

                    return JsonResponse({'message' : f'입고 처리가 {date} 기준으로 완료되었습니다.'}, status = 200)


                if is_inbound == 'False': # 출고 재품
                    if inventory.exists(): # 창고에 제품이 있는지 조회 '있으면'
                        before_quantity = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code, doc_no__lt = doc_no).last().after_quantity
                        after_quantity = int(before_quantity) - int(quantity)
                        
                    else: # 창조에 제품을 조회해 '없으면'
                        before_quantity = 0
                        after_quantity = int(before_quantity) - int(quantity)

                    InventorySheet.objects.create(
                        doc_no          = doc_no,
                        date            = date,
                        user_id         = user_id,
                        is_inbound      = is_inbound,
                        product_id      = product_id,
                        company_code    = company_code,
                        warehouse_code  = warehouse_code,
                        unit_price      = unit_price,
                        before_quantity = before_quantity,
                        after_quantity  = after_quantity,
                        quantity        = quantity,
                        etc             = etc
                    )

                    UPDATE_LIST = InventorySheet.objects.select_for_update(nowait= True).filter(product_id = product_id, warehouse_code = warehouse_code, doc_no__gt = doc_no).order_by('doc_no').values('doc_no')
            
                    UPDATED_LIST = []
                    # step 4 : 
                    for obj in UPDATE_LIST:
                        update_doc_no = obj.get('doc_no') 
                        UPDATED_LIST.append(update_doc_no)
            
                        before_doc_no = InventorySheet.objects.filter(doc_no__lt = update_doc_no).order_by('-doc_no').first().doc_no

                        before_query = InventorySheet.objects.get(doc_no = before_doc_no)
                        target_query = InventorySheet.objects.get(doc_no = update_doc_no)
                        
                        befoer_query_after_quantity = before_query.after_quantity
                        quantity =  target_query.quantity

                        if target_query.is_inbound == 'True': # 입고면 +, 출고면 -
                            target_query_after_quantity = befoer_query_after_quantity + quantity
                        else:
                            target_query_after_quantity = befoer_query_after_quantity - quantity
                        
                        InventorySheet.objects.filter(doc_no = update_doc_no).update(
                            before_quantity = befoer_query_after_quantity,
                            after_quantity = target_query_after_quantity, 
                            quantity = quantity
                        )

                return JsonResponse({'message' : f'출고 처리가 {date} 기준으로 완료되었습니다.'}, status = 200)
                    
        except KeyError:
            return JsonResponse({'message' : 'keyerror 발생'}, status = 200)

class ModifyInventorySheetView(View):
    def post(self, request):
        input_data = request.POST
        inventorysheet_doc_no = input_data.get('inventorysheet_doc_no', None)
        modify_quantity = input_data.get('quantity', None)


        target_data = InventorySheet.objects.get(doc_no= inventorysheet_doc_no)

        inventorysheet_id   = target_data.id
        product_id          = target_data.product_id
        warehouse_code      = target_data.warehouse_code
        before_quantity     = target_data.before_quantity
        after_quantity      = before_quantity + int(modify_quantity)
        date                = target_data.date
        
        try: 
            with transaction.atomic():
                # step 1 : 'inventorysheet_doc_no'의 수정 전 값들을  'InventorySheetLog'에 찍음
                InventorySheetLog.objects.create(
                    user_id         = 1,
                    process_type    = 'MODIFY',
                    date            = date,
                    inventorysheet_id = inventorysheet_id,
                    is_inbound      = target_data.is_inbound,
                    product_id      = target_data.product_id,
                    company_code    = target_data.company_code,
                    warehouse_code  = target_data.warehouse_code,
                    unit_price      = target_data.unit_price,
                    before_quantity = target_data.before_quantity,
                    after_quantity  = target_data.after_quantity,
                    quantity        = target_data.quantity,
                    etc             = target_data.etc,
                    status          = target_data.status,
                    created_at = target_data.created_at,
                    updated_at = target_data.updated_at
                )
                
                # step 2 : 기준이 되는 시트 수정 
                InventorySheet.objects.filter(doc_no = inventorysheet_doc_no).update(after_quantity = after_quantity, quantity = modify_quantity)

                # step 3 : 변경된 수량 반영 list 작성
                UPDATE_LIST = InventorySheet.objects.select_for_update(nowait= True).filter(
                    doc_no__gt = inventorysheet_doc_no,
                    product_id = product_id, 
                    warehouse_code = warehouse_code 
                    ).order_by('doc_no').values('doc_no')
            
                UPDATED_LIST = []
                # step 4 : list 기준으로 수정
                for obj in UPDATE_LIST:
                    update_doc_no = obj.get('doc_no') 
                    UPDATED_LIST.append(update_doc_no)
        
                    before_doc_no = InventorySheet.objects.filter(doc_no__lt = update_doc_no).order_by('-doc_no').first().doc_no

                    before_query = InventorySheet.objects.get(doc_no = before_doc_no)
                    target_query = InventorySheet.objects.get(doc_no = update_doc_no)
                    
                    befoer_query_after_quantity = before_query.after_quantity
                    quantity =  target_query.quantity

                    if target_query.is_inbound == 'True': # 입고면 +, 출고면 -
                        target_query_after_quantity = befoer_query_after_quantity + quantity
                    else:
                        target_query_after_quantity = befoer_query_after_quantity - quantity
                    
                    InventorySheet.objects.filter(doc_no = update_doc_no).update(
                        before_quantity = befoer_query_after_quantity,
                        after_quantity = target_query_after_quantity, 
                        quantity = quantity
                    )
                return JsonResponse({'message' : f"Inventory sheet ID {inventorysheet_doc_no} 을 기준으로 {UPDATED_LIST} 총 {len(UPDATED_LIST)}개의 sheet를 수정했습니다."}, status = 200)       
        except KeyError:
            return JsonResponse({'message' : '예외 사항 발생.'}, status = 403)
        

class DeleteInventorySheetView(View):
    def post(self, request):
        input_data = request.POST
        inventorysheet_doc_no = input_data.get('doc_no', None)
        
        delete_target = InventorySheet.objects.get(doc_no = inventorysheet_doc_no)

        inventorysheet_id = delete_target.id

        standard_proudct_id     = delete_target.product_id
        standard_warehouse_code = delete_target.warehouse_code
        change_before_quantity  = delete_target.before_quantity
        standartd_product_name  = Product.objects.get(id = standard_proudct_id).name
        
        # step 1 : 변경전 로그 찍기
        try:
            with transaction.atomic():
                InventorySheetLog.objects.create(
                            user_id = 1,
                            process_type = 'DELETE',
                            date            = delete_target.date,
                            inventorysheet_id = inventorysheet_id,
                            is_inbound      = delete_target.is_inbound,
                            product_id      = delete_target.product_id,
                            company_code    = delete_target.company_code,
                            warehouse_code  = delete_target.warehouse_code,
                            unit_price      = delete_target.unit_price,
                            before_quantity = delete_target.before_quantity,
                            after_quantity  = delete_target.after_quantity,
                            quantity        = delete_target.quantity,
                            etc             = delete_target.etc,
                            status          = delete_target.status,
                            created_at      = delete_target.created_at,
                            updated_at      = delete_target.updated_at)

                # step 2 : 삭제될 내용 수정 
                InventorySheet.objects.filter(doc_no = inventorysheet_doc_no).update(
                    before_quantity = change_before_quantity,
                    after_quantity  = change_before_quantity,
                    quantity = 0, 
                    status = False 
                )

                # step 3 : 삭제된 시트의 doc_no 기준으로 수정이 필요한 sheet 리스트 만듬
                UPDATE_LIST = InventorySheet.objects.select_for_update(nowait= True).filter(
                    product_id = standard_proudct_id, 
                    warehouse_code = standard_warehouse_code, 
                    doc_no__gt = inventorysheet_doc_no
                    ).order_by('doc_no').values('doc_no')
            
                UPDATED_LIST = []
                # step 4 : 만들어진 list를 기준으로 전부 수정
                for obj in UPDATE_LIST:
                    update_doc_no = obj.get('doc_no') 
                    UPDATED_LIST.append(update_doc_no)
        
                    before_doc_no = InventorySheet.objects.filter(doc_no__lt = update_doc_no).order_by('-doc_no').first().doc_no

                    before_query = InventorySheet.objects.get(doc_no = before_doc_no)
                    target_query = InventorySheet.objects.get(doc_no = update_doc_no)
                    
                    befoer_query_after_quantity = before_query.after_quantity
                    quantity =  target_query.quantity

                    if target_query.is_inbound == 'True': # 입고면 +, 출고면 -
                        target_query_after_quantity = befoer_query_after_quantity + quantity
                    else:
                        target_query_after_quantity = befoer_query_after_quantity - quantity
                    
                    InventorySheet.objects.filter(doc_no = update_doc_no).update(
                        before_quantity = befoer_query_after_quantity,
                        after_quantity = target_query_after_quantity, 
                        quantity = quantity
                    )
            return JsonResponse({'message' : f"삭제된 Inventory sheet ID {inventorysheet_id} 을 기준으로 창고 {standard_warehouse_code} 의 제품 [{standartd_product_name}] 포함된 {UPDATED_LIST} 총 {len(UPDATED_LIST)}개의 sheet를 수정했습니다."}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'keyError'}, status = 200)

class ListProductQuantityView(View):
    def get(self, request):
        product_quantity_list = list(TotalProductQuantity.objects.filter().values())

        return JsonResponse({'message' : product_quantity_list}, status = 200)

class ListProductPriceView(View):
    def get(self, request):
        product_price_list = list(ProductPrice.objects.filter().values())

        return JsonResponse({'message' : product_price_list}, status = 200)
