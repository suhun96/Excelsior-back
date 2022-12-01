import json, re

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection, IntegrityError
from django.db.models   import Q

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
        user_id = 1

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
        
        inventory = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code)
        
            # with transaction.atomic():
        if is_inbound == 'True': # 입고 상품
            if inventory.exists(): # 창고에 제품이 있는지 조회 '있으면'
                before_quantity = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code).last().after_quantity
                after_quantity = int(before_quantity) + int(quantity)
                
            else: # 창조에 제품을 조회해 '없으면'
                before_quantity = 0
                after_quantity = int(before_quantity) + int(quantity)
                
            InventorySheet.objects.create(
                user_id = user_id,
                is_inbound = is_inbound,
                product_id = product_id,
                company_code = company_code,
                warehouse_code = warehouse_code,
                unit_price = unit_price,
                before_quantity = before_quantity,
                after_quantity = after_quantity,
                quantity = quantity,
                etc = etc
            )
        
            return JsonResponse({'message' : '입고 처리가 완료되었습니다.'}, status = 200)

        if is_inbound == 'False': # 출고 재품
            if inventory.exists(): # 창고에 제품이 있는지 조회 '있으면'
                before_quantity = InventorySheet.objects.filter(product_id = product_id, warehouse_code = warehouse_code).last().after_quantity
                after_quantity = int(before_quantity) - int(quantity)
                
            else: # 창조에 제품을 조회해 '없으면'
                before_quantity = 0
                after_quantity = int(before_quantity) - int(quantity)

            InventorySheet.objects.create(
                user_id = user_id,
                is_inbound = is_inbound,
                product_id = product_id,
                company_code = company_code,
                warehouse_code = warehouse_code,
                unit_price = unit_price,
                before_quantity = before_quantity,
                after_quantity = after_quantity,
                quantity = quantity,
                etc = etc
            )
            
            return JsonResponse({'message' : '출고 처리가 완료되었습니다.'}, status = 200)   
        

class ModifyInventorySheetView(View):
    def post(self, request):
        input_data = request.POST
        inventorysheet_id = input_data.get('inventorysheet_id', None)
        quantity_s = input_data.get('quantity', None)


        target_data = InventorySheet.objects.get(id= inventorysheet_id)

        proudct_id = target_data.product_id
        warehouse_code = target_data.warehouse_code
        before_quantity = target_data.before_quantity
        after_quantity = before_quantity + int(quantity_s)
        
        try: 
            with transaction.atomic():
                # step 1 : 기준이 되는 시트(입력받는 id값 수정)
                InventorySheet.objects.filter(id = inventorysheet_id).update(after_quantity = after_quantity, quantity = quantity_s)
                
                # step 2 : 로그 작성 
                InventorySheetLog.objects.create(
                    user_id = 1,
                    process_type = 'modify',
                    inventorysheet_id = inventorysheet_id,
                    is_inbound = target_data.is_inbound,
                    product_id = target_data.product_id,
                    company_code = target_data.company_code,
                    warehouse_code = target_data.warehouse_code,
                    unit_price = target_data.unit_price,
                    before_quantity = target_data.before_quantity,
                    after_quantity = target_data.after_quantity,
                    quantity = target_data.quantity,
                    etc = target_data.etc,
                    status = target_data.status,
                    created_at = target_data.created_at,
                    updated_at = target_data.updated_at
                )
                
                # step 3 : index id 기준으로 수정되는 product_id, warehouse_code 수정
                UPDATE_LIST = list(InventorySheet.objects.select_for_update(nowait= True).filter(product_id = proudct_id, warehouse_code = warehouse_code, id__gt=inventorysheet_id).values('id'))

                UPDATED_LIST = []
                # step 4 : 구성된 UPDATE_LIST 차례 대로 수정.
                for obj in UPDATE_LIST:
                    update_id = obj.get('id') # 20 / 21 , 22, 23
                    UPDATED_LIST.append(update_id)
                    before_id = update_id - 1

                    before_query = InventorySheet.objects.get(id = before_id)
                    target_query = InventorySheet.objects.get(id = update_id)
                    
                    befoer_query_after_quantity = before_query.after_quantity
                    quantity =  target_query.quantity

                    if target_query.is_inbound == 'True': # 입고면 + 출고 =
                        target_query_after_quantity = befoer_query_after_quantity + quantity
                    else:
                        target_query_after_quantity = befoer_query_after_quantity - quantity
                    
                    InventorySheet.objects.filter(id = update_id).update(
                        before_quantity = befoer_query_after_quantity,
                        after_quantity = target_query_after_quantity, 
                        quantity = quantity
                    )
        except KeyError:
            return JsonResponse({'message' : '예외 사항 발생.'}, status = 403)
        
        return JsonResponse({'message' : f"Inventory sheet ID {inventorysheet_id} 을 기준으로 {UPDATED_LIST} 총 {len(UPDATED_LIST)}개의 sheet를 수정했습니다."}, status = 200)

class ListProductQuantityView(View):
    def get(self, request):
        product_quantity_list = list(TotalProductQuantity.objects.filter().values())

        return JsonResponse({'message' : product_quantity_list}, status = 200)

class ListProductPriceView(View):
    def get(self, request):
        product_price_list = list(ProductPrice.objects.filter().values())

        return JsonResponse({'message' : product_price_list}, status = 200)
<<<<<<< HEAD

class ListProductWarehouseView(View):
    def get(self, request):
        product_Warehouse_list = list(ProductWarehouse.objects.filter().values())

        return JsonResponse({'message' : product_Warehouse_list}, status = 200)

class ProductOutboundView(View):
    def post(self, request):
        input_data = request.POST
        product_id      = input_data.get('product_id', None)
        company_code    = input_data.get('company_code', None)
        warehouse_code  = input_data.get('warehouse_code', None)
        quantity        = input_data.get('quantity', None)
        unit_price      = input_data.get('unit_price', None)
        etc             = input_data.get('etc', None)

        if not Product.objects.filter(id = product_id).exists():
            return JsonResponse({'message' : '존재하지 않는 product id 입니다.'}, status = 403)

        if not company_code:
            return JsonResponse({'message' : '거래처가 입력되지 않았습니다.'}, status = 403)
        
        if not Company.objects.filter(code = company_code).exists():
            return JsonResponse({'message' : '거래처 코드가 존재하지 않습니다.'}, status = 403)

        if not warehouse_code: 
            return JsonResponse({'message' : '창고 코드가 입력되지 않았습니다.'}, statue = 403)

        if not Warehouse.objects.filter(code = warehouse_code).exists():
            return JsonResponse({'message' : '창고 코드가 존재하지 않습니다'}, statue = 403)

        if not quantity:
            return JsonResponse({'message' : '수량이 입력되지 않았습니다.'}, statue = 403)

        if not unit_price:
            return JsonResponse({'message' : '입고 가격이 입력되지 않았습니다.'}, statue = 403)

        if not etc:
            etc = ''

        try:
            with transaction.atomic():
                # step 1 입고
                ProductOutbound.objects.create(
                    unit_price = unit_price,
                    product_id = product_id,
                    company_code = company_code,
                    warehouse_code = warehouse_code,
                    quantity = quantity,
                    etc = etc
                )

                # step 2 창고수량 수정
                if ProductWarehouse.objects.get(product_id = product_id, warehouse_code = warehouse_code).stock_quantity == 0:
                    return JsonResponse({'message' : f'{warehouse_code}에 {product_id}상품의 수량을 확인해주세요.'}, status = 403)

                if not ProductWarehouse.objects.filter(product_id = product_id, warehouse_code = warehouse_code).exists():
                    return JsonResponse({'message' : f'{warehouse_code}에 {product_id}상품이 존재하지 않습니다.'}, status = 403)
                else:
                    before_stock_quantity = ProductWarehouse.objects.get(product_id = product_id, warehouse_code = warehouse_code).stock_quantity
                
                after_stock_quantity = int(before_stock_quantity) - int(quantity)
                
                ProductWarehouse.objects.update_or_create(product_id = product_id, warehouse_code = warehouse_code,
                    defaults={
                        'product_id' : product_id,
                        'warehouse_code' : warehouse_code,
                        'stock_quantity' : after_stock_quantity
                    })

                # step 3 최신 입고가 수정
                ProductPrice.objects.update_or_create(product_id =product_id, company_code = company_code,
                    defaults={
                        'product_id' : product_id,
                        'outbound_price' : unit_price
                    })

                # step 4 전체 제품 수량 체크
                stocks = ProductWarehouse.objects.filter(product_id = product_id).values('stock_quantity')

                sum_qauntity = 0
                
                for stock in stocks:
                    quantity = stock['stock_quantity']
                    sum_qauntity = sum_qauntity + quantity
            
                ProductQuantity.objects.update_or_create(product_id =product_id, 
                defaults= {
                    'product_id' : product_id,
                    'total_quantity' : sum_qauntity
                })
            return JsonResponse({'message' : '출고 처리가 완료되었습니다.'}, status = 200)    
        
        except:
            return JsonResponse({'message' : '출고 처리중 예외사항이 발생했습니다.'}, status = 403)

class SetProductionView(View):
    def post(self, request):
        input_data
        return 
=======
>>>>>>> 81329038cea85ca24a1715ade0f4246fd9ad7a1e
