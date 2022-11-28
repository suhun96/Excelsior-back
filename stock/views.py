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

class ProductInboundView(View):
    def get(self, request):
        product_inbound_list = list(ProductInbound.objects.filter().values())

        return JsonResponse({'message' : product_inbound_list}, status = 403)

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
                ProductInbound.objects.create(
                    unit_price = unit_price,
                    product_id = product_id,
                    company_code = company_code,
                    warehouse_code = warehouse_code,
                    quantity = quantity,
                    etc = etc
                )

                # step 2 창고수량 수정
                if not ProductWarehouse.objects.filter(product_id = product_id, warehouse_code = warehouse_code).exists():
                    before_stock_quantity = 0
                else:
                    before_stock_quantity = ProductWarehouse.objects.get(product_id = product_id, warehouse_code = warehouse_code).stock_quantity
                
                after_stock_quantity = int(before_stock_quantity) + int(quantity)
                
                ProductWarehouse.objects.update_or_create(product_id = product_id, warehouse_code = warehouse_code,
                    defaults={
                        'product_id' : product_id,
                        'warehouse_code' : warehouse_code,
                        'stock_quantity' : after_stock_quantity
                    })

                # step 3 최신 입고가 수정
                ProductPrice.objects.update_or_create( product_id =product_id, company_code = company_code,
                    defaults={
                        'product_id' : product_id,
                        'inbound_price' : unit_price
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
            return JsonResponse({'message' : '입고 처리가 완료되었습니다.'}, status = 200)    
        
        except:
            return JsonResponse({'message' : '입고 처리중 예외사항이 발생했습니다.'}, status = 403)

class ListProductQuantityView(View):
    def get(self, request):
        product_quantity_list = list(ProductQuantity.objects.filter().values())

        return JsonResponse({'message' : product_quantity_list}, status = 200)

class ListProductPriceView(View):
    def get(self, request):
        product_price_list = list(ProductPrice.objects.filter().values())

        return JsonResponse({'message' : product_price_list}, status = 200)

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
            return JsonResponse({'message' : '입고 처리가 완료되었습니다.'}, status = 200)    
        
        except:
            return JsonResponse({'message' : '입고 처리중 예외사항이 발생했습니다.'}, status = 403)

        
        
