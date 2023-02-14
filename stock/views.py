import json, re
import asyncio
from asgiref.sync import sync_to_async, async_to_sync

import time 

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


# deco
from users.decorator    import jwt_decoder
from products.utils     import telegram_bot
from .utils             import *

class CreateSheetView(View):
    @jwt_decoder
    @async_to_sync
    async def post(self, request):
        input_data = json.loads(request.body)
        user = request.user

        try:
            with transaction.atomic():
                new_sheet = create_sheet(input_data, user)
                new_sheet_id = new_sheet.id

                if new_sheet.type == 'inbound':
                    compositions = SheetComposition.objects.filter(sheet_id = new_sheet_id)

                    for composition in compositions:
                        product_id     = composition.product_id
                        warehouse_code = composition.warehouse_code
                        quantity       = composition.quantity
                        unit_price     = composition.unit_price 

                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        if not stock.exists():
                            before_quantity = 0

                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                        
                        stock_quantity  = before_quantity + int(quantity)
                            
                        # else:
                        #     stock_quantity  = int(quantity)

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = new_sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})
                        
                        # product_serial_generate
                        if Product.objects.get(id = product_id).is_serial == True:
                            create_product_serial_code(product_id, quantity, new_sheet_id)
                        else:
                            pass

                        # 이동 평균법 작동
                        mam_create_sheet(product_id, unit_price, quantity, stock_quantity)

                    register_checker(input_data)
                    await telegram_bot(new_sheet_id)

                    return JsonResponse({'message' : '입고 성공', 'sheet_id' : new_sheet_id}, status = 200)

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
                        
                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        if not stock.exists():
                            before_quantity = 0

                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                        
                        stock_quantity  = before_quantity - int(quantity)
                        # else:
                        #     stock_quantity  = int(quantity)                            

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                            sheet_id = new_sheet_id,
                            stock_quantity = stock_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})
                        
                    register_checker(input_data)
                    await telegram_bot(new_sheet_id)
    
                    return JsonResponse({'message' : '출고 성공', 'sheet_id' : new_sheet_id}, status = 200)
                
                if new_sheet.type == 'return':
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
                            defaults={'total_quantity' : stock_quantity})

                    
                    
                    return JsonResponse({'message' : '반품 성공', 'sheet_id' : new_sheet_id}, status = 200)
        except Exception as e:
            return JsonResponse({'message' : e} , status = 403)
            
class ModifySheetView(View):
    def check_serial_code(self, sheet_id):
        if SerialCode.objects.filter(sheet_id= sheet_id).exists():
            return True
        else:
            return False

    @jwt_decoder
    def post(self, request):
        modify_user = request.user
        modify_data = json.loads(request.body)
        # 들어온 데이터 양식 확인.
        
        
        sheet_id = modify_data.get('sheet_id')
        
        try:
            with transaction.atomic():
                # sheet, sheet_detail log 작성
                create_sheet_logs(sheet_id, modify_user)
                
                # sheet_detail 롤백 [입고 = (-), 출고 = (+)]
                rollback_sheet_detail(sheet_id) # 이부분에서 이동 평균법 수정(delete).
                
                # sheet 수정    
                modify_sheet_data(sheet_id, modify_user, modify_data)

                target_sheet_type = Sheet.objects.get(id = sheet_id).type 
                
                if target_sheet_type == 'inbound':
                    Delete_sheet_composition = SheetComposition.objects.filter(sheet_id = sheet_id).delete()
                    Delete_sheet_serialcode = SerialCode.objects.filter(sheet_id = sheet_id).delete()
                    Modify_sheet_detail = modify_sheet_detail(sheet_id, modify_data['products'])
                    Reflecte_sheet_detail = reflecte_sheet_detail(sheet_id) # 이 부분에서 이동 평균법 재 생성(create)
                    Register_check = register_checker(modify_data)
                    

                elif target_sheet_type == 'outbound':
                    Delete_sheet_composition = SheetComposition.objects.filter(sheet_id = sheet_id).delete()
                    Delete_sheet_serialcode = SerialCode.objects.filter(sheet_id = sheet_id).delete()
                    Modify_sheet_detail = modify_sheet_detail(sheet_id, modify_data['products'])
                    Reflecte_sheet_detail = reflecte_sheet_detail(sheet_id)
                    Register_check = register_checker(modify_data)

                elif target_sheet_type in ['return', 'new']:
                    # sheet_detail 삭제
                    SheetComposition.objects.filter(sheet_id = sheet_id).delete()
                    # 연결된 serial_code 도 삭제
                    SerialCode.objects.filter(sheet_id = sheet_id).delete()
                    # 수정된 sheet_detail 생성
                    modify_sheet_detail(sheet_id, modify_data['products'])
                    # 수정된 sheet_detail 수량 반영 / 수정된 sheet_detail 중 is_serial이 True 인 product 시리얼 코드 자동 생성.
                    reflecte_sheet_detail(sheet_id)
                    # 수정된 가격 반영
                    register_checker(modify_data)

                else:
                    modify_sheet_detail_2(sheet_id, modify_data['products'])
                    register_checker(modify_data)

                check_serial_code = self.check_serial_code(sheet_id) 
                if check_serial_code == True:
                    return JsonResponse({'message' : 'serial code가 입력된 sheet 입니다. 업데이트 내역을 확인해 주세요.'}, status = 200)
                else:
                    return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class DeleteSheetView(View):
    @jwt_decoder
    def post(self, request):
        delete_user = request.user
        sheet_id = request.POST['sheet_id']
        
        try:
            with transaction.atomic():
                # sheet, sheet_detail log 작성
                create_sheet_logs(sheet_id, delete_user)
                # 롤백
                rollback_sheet_detail(sheet_id)
                # Sheet_detail 삭제
                SheetComposition.objects.filter(sheet_id = sheet_id).delete()
                # type 변환
                Sheet.objects.filter(id = sheet_id).update(type = "delete")

                return JsonResponse({'message' : 'sheet 삭제 완료'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

# class ModifySheetEtcView(View):
#     @jwt_decoder
#     def post(self, request):
#         modify_user = request.user
#         modify_data = json.loads(request.body)
#         # 들어온 데이터 양식 확인.
#         sheet_id = modify_data.get('sheet_id')
#         modified_etc = modify_data.get('etc')
#         try:
#             with transaction.atomic():             
#                 # sheet 수정    
#                 target = Sheet.objects.filter(id = sheet_id)
#                 target.etc = modified_etc
#                 target.save()
#                 return JsonResponse({'message' : '수정 완료'}, status = 200)
#         except:
#             return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class GetSheetEtcView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id', None)
        result = Sheet.objects.filter(id = sheet_id)
        return JsonResponse({'message' : result}, status = 200)

class InquireSheetLogView(View):
    def get(self, request):
        result = list(SheetLog.objects.all().values())

        return JsonResponse({'message' : result}, status = 200)

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
        offset         = int(request.GET.get('offset'))
        limit          = int(request.GET.get('limit'))
        name           = request.GET.get('user_name', None)
        stock_type     = request.GET.get('type', None)
        date_start     = request.GET.get('date_start', None)
        date_end       = request.GET.get('date_end', None)
        company_name   = request.GET.get('company_name', None)
        stock_type     = request.GET.get('type', None)

        q = Q(date__range = (date_start, date_end))

        if stock_type:
            q &= Q(type__icontains = stock_type)
        if name:
            user_id = User.objects.get(name = name).id
            q &= Q(user_id__exact = user_id)
        if company_name:
            company_id = Company.objects.get(name = company_name).id
            q &= Q(company_id = company_id)

        
        sheets = Sheet.objects.filter(q).order_by('-date', '-id')[offset : offset+limit].values(
            'id',       
            'type',
            'user__name',
            'date',
            'company_id',
            'company__name',
            'company__code',
            'etc',
            'document_num',
            'related_sheet_id',
            'created_at',
            'updated_at'
        )
        
        return JsonResponse({'message' : list(sheets)}, status = 200)

class InfoSheetListView(View):
    def get(self, request):
        # sheet
        sheet_id       = request.GET.get('sheet_id', None)
        name           = request.GET.get('user_name', None)
        stock_type     = request.GET.get('type', None)
        date_start     = request.GET.get('date_start', None)
        date_end       = request.GET.get('date_end', None)
        company_name   = request.GET.get('company_name', None)
        # sheet-detail 
        product_id   = request.GET.get('product_id', None)
        product_group_id = request.GET.get('product_group_id', None)
        
        if sheet_id:
            sheet_detail = SheetComposition.objects.filter(sheet_id = sheet_id).values(
                'id', 
                'sheet_id',
                'sheet__document_num',
                'sheet__user__name',
                'sheet__type',
                'sheet__company_id',
                'sheet__company__name',
                'sheet__company__code',
                'sheet__etc',
                'sheet__date',
                'sheet__related_sheet_id',
                'sheet__created_at',
                'product_id',
                'product__is_serial',
                'product__name',
                'product__company__code',
                'product__product_code',
                'product__barcode',
                'product__product_group__name',
                'unit_price',
                'quantity',
                'warehouse_code',
                'location',
                'etc'
            )

            return JsonResponse({'message' : list(sheet_detail)}, status = 200)

        else:
            offset = int(request.GET.get('offset'))
            limit  = int(request.GET.get('limit'))

            if not date_start:
                return JsonResponse({'message' : "기준 시작 날짜 설정 오류"}, status = 403)
            if not date_end:
                return JsonResponse({'message' : "기준 종료 날짜 설정 오류"}, status = 403)
            
            # Sheet 필터링
            q = Q(sheet__date__range = (date_start, date_end))
            # q = Q(sheet__date__range = (date_start, date_end), sheet__type__in = ['inbound', 'outbound', 'generate', 'new'])

            if name:
                try:
                    user_id = User.objects.get(name = name).id
                except User.DoesNotExist:
                    return JsonResponse({'message' : '존재하지 않는 유저입니다.' }, status = 403)
                q &= Q(sheet__user_id__exact = user_id)
            if stock_type:
                q &= Q(sheet__type = stock_type)
            if product_id:
                product_id = Product.objects.get(id = product_id).id
                q &= Q(product_id = product_id)
            if company_name:
                company_id = Company.objects.get(name = company_name).id
                q &= Q(sheet__company_id = company_id)
            if product_group_id:
                product_id_list = Product.objects.filter(product_group_id = product_group_id).values_list('id', flat = True)
                q &= Q(product_id__in = product_id_list)
            
            sheet_detail = SheetComposition.objects.filter(q).order_by('-sheet__date', '-id')[offset : offset+limit].values(
                'id', 
                'sheet_id',
                'sheet__document_num',
                'sheet__user__name',
                'sheet__type',
                'sheet__company_id',
                'sheet__company__name',
                'sheet__company__code',
                'sheet__etc',
                'sheet__date',
                'sheet__related_sheet_id',
                'sheet__created_at',
                'product_id',
                'product__is_serial',
                'product__name',
                'product__company__code',
                'product__product_code',
                'product__barcode',
                'product__product_group__name',
                'unit_price',
                'quantity',
                'warehouse_code',
                'location',
                'etc'
                )
            
        
            return JsonResponse({'message' : list(sheet_detail) }, status = 200)

class ClickSheetView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id', None)

        if not sheet_id:
            return JsonResponse({'message' : 'sheet id 가 입력되지 않았습니다.'}, status = 200)

        compositions = SheetComposition.objects.filter(sheet_id = sheet_id)

        for_list = []
        for composition in compositions:
            product = Product.objects.get(id = composition.product_id)
            try:
                total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))
            except QuantityByWarehouse.DoesNotExist:
                total = 0
            serial_codes = SerialCode.objects.filter(sheet_id = sheet_id ,product_id = product.id).values_list('code', flat= True)
            
            if product.company_id == "" :
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : product.product_group__name,
                    'barcode'               : product.barcode,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_code'        : composition.warehouse_code,
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list(serial_codes),
                    'etc'                   : composition.etc   
                } 
            else:
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : product.product_group__name,
                    'barcode'               : product.barcode,
                    'company_id'            : product.company.id,
                    'company_name'          : product.company.name,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_code'        : composition.warehouse_code,
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list(serial_codes),
                    'etc'                   : composition.etc   
                }

            for_list.append(dict)

        return JsonResponse({'message' : for_list}, status = 200)
    
class TotalQuantityView(View):
    def get(self, request):
        warehouse_code = request.GET.get('warehouse_code', None)

        result_list = []

        if warehouse_code:
            check = QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code)

            for obj in check:
                get_product = Product.objects.get(id = obj.product_id)
                try: 
                    MAM = MovingAverageMethod.objects.get(product_id = obj.product_id)
                    average_price = MAM.average_price
                    custom_price = MAM.custom_price
                except MovingAverageMethod.DoesNotExist:
                    average_price = 0
                    custom_price = 0

                dict = {
                    'product_code' : get_product.product_code,
                    'product_name' : get_product.name,
                    'warehouse_code' : obj.warehouse_code,
                    'warehouse_name' : Warehouse.objects.get(code = obj.warehouse_code).name,
                    'status'       : get_product.status,
                    'safe_quantity': get_product.safe_quantity,
                    'quantity'     : obj.total_quantity,
                    'average_price' : average_price,
                    'custom_price' : custom_price,
                    'ketword'      : get_product.keyword
                }
                result_list.append(dict) 
            return JsonResponse({'message': result_list})
        
        else:
            ids = []
            
            for product_id in QuantityByWarehouse.objects.all().values('product'):
                ids.append(product_id['product'])

            for num in set(ids):
                get_product = Product.objects.get(id = num)
                check = QuantityByWarehouse.objects.filter(product_id = num).aggregate(quantity = Sum('total_quantity'))
                try: 
                    MAM = MovingAverageMethod.objects.get(product_id = num)
                    average_price = MAM.average_price
                    custom_price = MAM.custom_price
                except MovingAverageMethod.DoesNotExist:
                    average_price = 0
                    custom_price = 0
                dict = {
                    'product_code' : get_product.product_code,
                    'product_name' : get_product.name,
                    'product_group_name' : get_product.product_group.name,
                    'status'       : get_product.status,
                    'safe_quantity': get_product.safe_quantity,
                    'quantity'     : check['quantity'],
                    'average_price' : average_price,
                    'custom_price' :  custom_price,
                    'ketword'      : get_product.keyword
                }
                result_list.append(dict) 
            return JsonResponse({'message': result_list})

class PriceCheckView(View):
    def post(self, request):
        input_data = request.POST
        
        try:
            company_id = input_data['company_id']
            product_id   = Product.objects.get(product_code = input_data['product_code']).id
            
            type         = input_data['type']
            
            if type == 'inbound':
                price = ProductPrice.objects.get(company_id = company_id, product_id = product_id).inbound_price
            
            if type == 'outbound':
                price = ProductPrice.objects.get(company_id = company_id, product_id = product_id).outbound_price
        
            return JsonResponse({'message' : f'{price}'}, status = 200)
        
        
        except Product.DoesNotExist:    
            return JsonResponse({'message' : '잘못된 요청을 보내셨습니다.2'}, status = 403)
        except ProductPrice.DoesNotExist:
            return JsonResponse({'message' : '0' }, status = 200)
        
class SerialCodeCheckView(View):
    def serial_product_code_checker(self, serial_code):
        product_id = SerialCode.objects.get(code = serial_code).product_id

        product_code = Product.objects.get(id = product_id).product_code
        return product_code

    def serial_tracker(self, serial_code):
        sheet_id = SerialCode.objects.filter(code = serial_code).latest('id').sheet_id

        sheet = Sheet.objects.get(id = sheet_id )

        return sheet

    def print_sheet(self, sheet, serial_code):
        product_id = SerialCode.objects.filter(code = serial_code).latest('id').product_id
        
        sheet_composition = SheetComposition.objects.filter(sheet_id = sheet.id , product_id = product_id)
        
        product = Product.objects.get(id = product_id)

        result = []

        for detail in sheet_composition:
            try: 
                total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))
        
                partial_quantity = QuantityByWarehouse.objects.get(warehouse_code = detail.warehouse_code, product_id = product.id).total_quantity,
            
            except QuantityByWarehouse.DoesNotExist:
                partial_quantity = 0
                total = 0
            
            dict_A = {
                'sheet_id'              : sheet.id,
                'related_sheet_id'      : sheet.related_sheet_id,
                'document_num'          : sheet.document_num,
                'user_name'             : sheet.user.name,
                'type'                  : sheet.type,
                'company_name'          : sheet.company.name,
                'etc'                   : sheet.etc,
                'created_at'            : sheet.created_at,
                'is_serial'             : product.is_serial,
                'product_code'          : product.product_code,
                'product_name'          : product.name,
                'product_group_name'    : product.product_group.name,
                'barcode'               : product.barcode,
                'unit_price'            : detail.unit_price,
                'quantity'              : detail.quantity,
                'total_quantity'        : total['total_quantity__sum'],
                'partial_quantity'      : partial_quantity,
                'location'              : detail.location,
                'etc'                   : detail.etc   
                }
            result.append(dict_A) 
        
        return result

    def get(self, request):
        serial_code  = request.GET.get('serial_code')
        process_type = request.GET.get('process_type')

        if process_type == "generate":
            set_product_code = request.GET.get('set_product_code', None)

            if not set_product_code:
                return JsonResponse({'message' : '생산 시리얼 코드 체크를 위해서는 set_product_code가 필요합니다.'}, status = 403)

            if not SerialCode.objects.filter(code = serial_code).exists(): 
                return JsonResponse({'message' : '존재하지 않는 시리얼 입니다.'}, status = 403)
            
            else:
                set_product_id = Product.objects.get(product_code = set_product_code).id
                component_ids = ProductComposition.objects.filter(set_product_id = set_product_id).values_list('composition_product', flat= True)
                
                target_product_id = SerialCode.objects.filter(code = serial_code).last().product_id
                
                if not target_product_id in component_ids:
                    return JsonResponse({'message' : '구성품의 시리얼 코드가 아닙니다.'}, status = 403)

                sheet = self.serial_tracker(serial_code)
                sheet_type = sheet.type
                
                if sheet_type == 'new':
                    return JsonResponse({'message' : '생산 처리가 가능합니다.'}, status = 200)

                if sheet_type == 'generate':
                    return JsonResponse({'message' : '생산 처리가 가능합니다.'}, status = 200)

                if sheet_type == 'inbound':
                    return JsonResponse({'message' : '생산 처리가 가능합니다.'}, status = 200)
                
                if sheet_type == 'used':
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '이미 출고된 시리얼 입니다.', 'result': result }, status = 403)

                if sheet_type == 'outbound':
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '이미 출고된 시리얼 입니다.', 'result': result }, status = 403)
                
                return JsonResponse({'message' : '생산 처리가 가능합니다.'}, status = 200)

        if process_type == 'inbound':
            if not SerialCode.objects.filter(code = serial_code).exists():
                return JsonResponse({'message' : '입고 처리가 가능합니다.'}, status = 200)
            
            else:
                sheet = self.serial_tracker(serial_code)
                sheet_type  = sheet.type
                
                if sheet_type == 'inbound':
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '보유하고 있는 시리얼 입니다.', 'result': result}, status = 403)

                if sheet_type == 'generate':
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '보유하고 있는 시리얼 입니다.', 'result': result}, status = 403)
        
                else:
                    return JsonResponse({'message' : '입고 처리가 가능합니다.'}, status = 200)

        if process_type == 'outbound':
            if not SerialCode.objects.filter(code = serial_code).exists():
                return JsonResponse({'message' : '존재하지 않는 시리얼입니다.'}, status = 403)

            else:
                sheet = self.serial_tracker(serial_code)
                sheet_type  = sheet.type

                if sheet_type == "new":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.' , 'product_code' : product_code}, status = 200)

                if sheet_type == "inbound":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.' , 'product_code' : product_code}, status = 200)

                if sheet_type == "generate":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.', 'product_code' : product_code}, status = 200)

                if sheet_type == "outbound":
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '이미 출고된 시리얼 입니다.', 'result': result }, status = 403)

                if sheet_type == "used":
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '이미 세트 생산에 사용된 시리얼 입니다.', 'result': result }, status = 403)

class StockTotalView(View):
    def get(self, request):
        product_name    = request.GET.get('product_name', None)
        product_code    = request.GET.get('product_code', None)
        keyword         = request.GET.get('keyword', None)
        barcode         = request.GET.get('barcode', None)
        type            = request.GET.get('type', None)
        company_id      = request.GET.get('company_id', None)
        warehouse_code  = request.GET.get('warehouse_code', None)
        status          = request.GET.get('status', None)

        q = Q()
        if product_name:
            q &= Q(name__icontains = product_name)
        if product_code:
            q &= Q(product_code__icontains = product_code)
        if barcode:
            q &= Q(barcode__icontains = barcode)
        if keyword:
            q &= Q(keyword__icontains = keyword)
        if status:
            q &= Q(status = status)

        target_products = Product.objects.filter(q)

        result = []

        try:
            for product in target_products:
                list_A = QuantityByWarehouse.objects.filter(product_id = product.id)
                
                total_quantity = 0
                for obj in list_A:
                    total_quantity += obj.total_quantity

                price = 0
                if type == 'inbound':
                    if not company_id:
                        price = 0
                    else:
                        try:
                            check_price = ProductPrice.objects.get(company_id = company_id, product_id = product.id)
                            price = check_price.inbound_price
                        except ProductPrice.DoesNotExist:
                            price = 0

                if type == 'outbound':
                    if not company_id:
                        price = 0
                    else:
                        try:
                            check_price = ProductPrice.objects.get(company_id = company_id, product_id = product.id)
                            price = check_price.outbound_price
                        except ProductPrice.DoesNotExist:
                            price = 0
                
                if not warehouse_code:
                    try:
                        partial_quantity = QuantityByWarehouse.objects.get(product_id = product.id, warehouse_code = product.warehouse_code).total_quantity
                    except QuantityByWarehouse.DoesNotExist:
                        partial_quantity = 0
                    dict = {
                        'is_serial'         : product.is_serial,
                        'product_name'      : product.name,
                        'product_code'      : product.product_code,
                        'warehouse_name'    : Warehouse.objects.get(code =product.warehouse_code).name,
                        'warehouse_code'    : product.warehouse_code,
                        'location'          : product.location,
                        'partial_quantity'  : partial_quantity,
                        'total_quantity'    : total_quantity,
                        'latest_price'      : price,
                        'status'            : product.status
                    }
                else:
                    try:
                        partial_quantity = QuantityByWarehouse.objects.get(product_id = product.id, warehouse_code = product.warehouse_code).total_quantity
                    except QuantityByWarehouse.DoesNotExist:
                        partial_quantity = 0
                    
                    dict = {
                        'is_serial'         : product.is_serial,
                        'product_name'      : product.name,
                        'product_code'      : product.product_code,
                        'warehouse_name'    : Warehouse.objects.get(code = warehouse_code).name,
                        'warehouse_code'    : warehouse_code,
                        'location'          : product.location,
                        'partial_quantity'  : partial_quantity,
                        'total_quantity'    : total_quantity,
                        'latest_price'      : price,
                        'status'            : product.status
                    }
                result.append(dict)
            
            return JsonResponse({'message' : result})
        except Product.DoesNotExist:    
            return JsonResponse({'message' : '잘못된 요청을 보내셨습니다.2'}, status = 403)
        except ProductPrice.DoesNotExist:
            return JsonResponse({'message' : '0' }, status = 403)

# Serial Code - Title
class CreateSerialCodeTitleView(View):
    def post(self, request):
        title = request.POST['title']

        new_title = SerialCodeTitle.objects.create(title = title)

        return JsonResponse({'message' : '새로운 title이 생성 되었습니다.'}, status = 200)

class ModifySerialCodeTitleView(View):
    def post(self, request):
        title_id = request.POST['title_id']

        UPDATE_SET = {}

        for key, value in request.POST.items():
            if key == 'title':
                UPDATE_SET.update({key : value})
            
            if key == 'status':
                if value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                UPDATE_SET.update({key : value})
        
        try:
            with transaction.atomic():
                SerialCodeTitle.objects.filter(id = title_id).update(**UPDATE_SET)
            return JsonResponse({'message' : '커스텀 타이틀 수정을 성공했습니다.'}, status = 200)
        except SerialCodeTitle.DoesNotExist:
            return JsonResponse({'message' : f'title id를 확인해주세요. {title_id}'}, status = 403)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)      

class InquireSerialCodeTitleView(View):
    def get(self, request):
        
        Title_list = list(SerialCodeTitle.objects.all().values())

        return JsonResponse({'message': Title_list})

# Serial Code - Value
class CreateSerialCodeValueView(View):
    @jwt_decoder
    def post(self, request):
        user = request.user
        serial_code_title_id = request.POST['title_id']
        serial_code          = request.POST['serial_code']
        contents             = request.POST['contents']
        
        serial_code_id = SerialCode.objects.filter(code = serial_code).last().id

        try:
            with transaction.atomic():
                obj, check = SerialCodeValue.objects.update_or_create(
                    title_id       = serial_code_title_id,
                    serial_code_id = serial_code_id,
                    defaults= {
                        'contents' : contents,
                        'user_id'  : user.id
                    })
                
                tartget = SerialCodeValue.objects.get(id = obj.id)
                tartget.date = datetime.now()
                tartget.save()

                if check == True:
                    return JsonResponse({'message' : '생성 성공'}, status = 200)
                else:
                    return JsonResponse({'message' : '수정 성공'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '잘못된 key 값을 입력하셨습니다.'}, status = 403)

class DeleteSerialCodeValueView(View):
    def get(self, request):
        value_id = request.GET.get('value_id')
        try:
            SerialCodeValue.objects.get(id = value_id).delete()

            return JsonResponse({'message' : '삭제가 완료되었습니다.'}, status = 200)
        except SerialCodeValue.DoesNotExist:
            return JsonResponse({'message' : '존재하지 않는 ID 값 입니다.'}, status = 403)

# Serial Code - 조회
class InquireSerialCodeView(View):
    def get(self, request):
        target_sheet_id = request.GET.get('sheet_id', None)
        target_product_id = request.GET.get('product_id', None)
        
        try:
            if not target_sheet_id:
                raise KeyError
            if not target_product_id:
                raise KeyError

            serial_code_list = list(SerialCode.objects.filter(sheet_id = target_sheet_id, product_id = target_product_id).values_list('code', flat= True))

            return JsonResponse({'message' : serial_code_list}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '입력해주신 값에 오류가 있습니다.[ sheet_id, product_id ]'}, status = 403)
        except SerialCode.DoesNotExist:
            return JsonResponse({'message' : '검색 조건에 맞는 시리얼 코드가 없습니다.'}, status = 403)    

class InquireSetSerialCodeView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id')
        list_id = SerialCode.objects.filter(sheet_id = sheet_id).values_list('id', flat = True)


        result = []
        for set_serial_code_id in list_id:
            set_serial_code = SerialCode.objects.get(id = set_serial_code_id).code
            list_D = list(SetSerialCodeComponent.objects.filter(set_serial_code_id = set_serial_code_id).values_list('component_serial_code__code', flat = True))
            
            send_form = { 'generate_serial_code' : set_serial_code, 'used_serial_code' : list_D}
            
            result.append(send_form)
            
        return JsonResponse({'message' : result}, status =200)

class CheckSetProductView(View):
    def get(self, request):
        set_product_code = request.GET.get('set_product_code')
        
        set_proudct_info = Product.objects.get(product_code = set_product_code)
        
        component_ids = ProductComposition.objects.filter(set_product_id = set_proudct_info.id).values_list('composition_product', flat= True)
        RESULT_LIST = []

        for id in component_ids:
            product_info = Product.objects.get(id = id)
            
            try: 
                total = QuantityByWarehouse.objects.filter(product_id = product_info.id).aggregate(Sum('total_quantity'))
            except QuantityByWarehouse.DoesNotExist:
                total = 0

            warehouse_by_quantity = QuantityByWarehouse.objects.filter(product_id = product_info.id)
            WBQ_dict = []
            for WBQ in warehouse_by_quantity:
                WBQ_dict.append({
                    'warehouse_code'   : WBQ.warehouse_code,
                    'warehouse_name'   : Warehouse.objects.get(code = WBQ.warehouse_code).name,
                    'partial_quantity' : WBQ.total_quantity
                })

            conponents_dict = {
                'is_serial'         : product_info.is_serial,
                'product_group_name': product_info.product_group.name,
                'product_name'      : product_info.name,
                'product_code'      : product_info.product_code,
                'WBQ'               : WBQ_dict,
                'total_quantity'    : total['total_quantity__sum'],
                'required_quantity' : ProductComposition.objects.get(set_product_id= set_proudct_info.id , composition_product_id = id).quantity
            }
            
            RESULT_LIST.append(conponents_dict)

        return JsonResponse({'message' : RESULT_LIST}, status = 200)

class GenerateSetProductView(View):
    def bind_used_generate_sheet(self, generate_sheet_id, used_sheet_id):
        generate_sheet = Sheet.objects.get(id = generate_sheet_id)
        generate_sheet.related_sheet_id = used_sheet_id
        used_sheet = Sheet.objects.get(id = used_sheet_id)
        used_sheet.related_sheet_id = generate_sheet_id
        generate_sheet.save()
        used_sheet.save()

    def generate_sheet(self, input_data, user):
        user = user
        input_data = input_data

        input_user =  user.id
    
        input_date = input_data.get('date', None)
        input_etc  = input_data.get('etc', None)
        
        # 세트 생산에 사용.
        set_product_code     = input_data.get('set_product_code')
        manufacture_quantity = input_data.get('manufacture_quantity')
        warehouse_code       = input_data.get('warehouse_code')
        
        # 세트 생산에 etc를 기입하지 않을 때 빈값으로 넣는다.
        if not input_etc:
            input_etc = ""

        try:
            with transaction.atomic():
                generate_sheet = Sheet.objects.create(
                    user_id = input_user,
                    type = 'generate',
                    company_id = 1,
                    date = input_date,
                    etc  = input_etc
                )

                generate_document_num(generate_sheet.id )            

                generate_sheet_id = generate_sheet.id
                
                try:           
                    set_product  = Product.objects.get(product_code = set_product_code)
                except Product.DoesNotExist:
                    return JsonResponse({'message' : f'{set_product_code}는 존재하지 않습니다.'}, status = 403) 

                if set_product.is_set == False:
                    return JsonResponse({'message' : f'이 상품은 세트가 아닙니다. 생산 불가능 합니다.'}, status = 403) 
                
                ### 이동 평균법으로 가격을 가져오자.
                
                component_list = ProductComposition.objects.filter(set_product_id = set_product.id).values_list('composition_product', flat= True) 
                
                generate_set_product_price = 0
                for component_id in component_list:
                    
                    try:
                        mam_price = MovingAverageMethod.objects.get(product_id = component_id)
                        # 수량만큼 추가로 계산
                        quantity_2 = ProductComposition.objects.get(set_product_id = set_product.id, composition_product_id = component_id).quantity
                        if mam_price.custom_price == 0:
                            target_price = mam_price.average_price * quantity_2
                        else:
                            target_price = mam_price.custom_price * quantity_2
                    except MovingAverageMethod.DoesNotExist:
                        target_price = 0
                    
                    generate_set_product_price += target_price

                labor_price = set_product.labor
                total_price = generate_set_product_price + labor_price 
                

                generate_sheet_composition = SheetComposition.objects.create(
                    sheet_id        = generate_sheet.id,
                    product_id      = set_product.id,
                    quantity        = manufacture_quantity, 
                    warehouse_code  = warehouse_code,
                    unit_price      = total_price,
                    etc             = f'세트를 생산했습니다.{generate_sheet_id}'
                )
                
                # 수량 반영
                stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = set_product.id)
                        
                if stock.exists():
                    before_quantity = stock.last().stock_quantity
                    stock_quantity  = before_quantity + int(manufacture_quantity)
                else:
                    stock_quantity  = int(manufacture_quantity)

                StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = set_product.id).create(
                    sheet_id = generate_sheet.id,
                    stock_quantity = stock_quantity,
                    product_id = set_product.id,
                    warehouse_code = warehouse_code )
                
                QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = set_product.id).update_or_create(
                    product_id = set_product.id,
                    warehouse_code = warehouse_code,
                    defaults={'total_quantity' : stock_quantity})

                # 이동 평균법 적용
                # mam_create_sheet(product_id, unit_price, quantity, stock_quantity)
                
                mam_create_sheet(set_product.id, total_price, int(manufacture_quantity), stock_quantity)

                
            return generate_sheet_id
        except:
            raise Exception({'message' : 'generate_sheet를 생성하는중 에러가 발생했습니다.'})
    
    def used_sheet(self, input_data, user, generate_sheet_id):
        components = input_data.get('components')
        input_date = input_data.get('date', None)

        generate_sheet_id = generate_sheet_id

        try:
            with transaction.atomic():
                used_sheet = Sheet.objects.create(
                    user_id = user.id,
                    type = 'used',
                    company_id = 1,
                    date = input_date,
                    etc  = '세트 생산으로 인한 소진'
                )

                generate_document_num(used_sheet.id )
                
                used_sheet_id = used_sheet.id

                total_used_serial = []

                for component in components:
                    
                    component_serial_codes = []

                    for used_product in  component:
                        used_product_id = Product.objects.get(product_code = used_product.get('product_code')).id
                        try:
                            check_price = MovingAverageMethod.objects.get(product_id = used_product_id)

                            if check_price.custom_price == 0:
                                unit_price = check_price.average_price
                            else:
                                unit_price = check_price.custom_price
                        except MovingAverageMethod.DoesNotExist:
                            unit_price = 0

                        SheetComposition.objects.create(
                            sheet_id        = used_sheet.id,
                            product_id      = used_product_id,
                            quantity        = used_product.get('quantity'), 
                            warehouse_code  = used_product.get('warehouse_code'),
                            unit_price      = unit_price,
                            etc             = '세트 생산으로 인한 소진'
                        )
                    
                        # 시리얼 코드 체크
                        if 'serials' in used_product:
                            count_serial_code(input_data, used_product, used_sheet)
                            serials = used_product.get('serials')
                            component_serial_codes.extend(serials)

                        # 수량 반영
                        stock = StockByWarehouse.objects.filter(warehouse_code = used_product.get('warehouse_code'), product_id = used_product_id)
                    
                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                            stock_quantity  = before_quantity - int(used_product.get('quantity'))
                        else:
                            stock_quantity  = int(used_product.get('quantity'))

                        StockByWarehouse.objects.filter(warehouse_code = used_product.get('warehouse_code'), product_id = used_product_id).create(
                            sheet_id = used_sheet.id,
                            stock_quantity = stock_quantity,
                            product_id = used_product_id,
                            warehouse_code = used_product.get('warehouse_code') )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = used_product.get('warehouse_code'), product_id = used_product_id).update_or_create(
                            product_id = used_product_id,
                            warehouse_code = used_product.get('warehouse_code'),
                            defaults={'total_quantity' : stock_quantity})
                    
                    total_used_serial.append(component_serial_codes)
                    
            return used_sheet_id, total_used_serial
        except Exception:
            raise Exception({'message' : 'used_sheet를 생성하는중 에러가 발생했습니다.'})

    def bind_set_serial_code(self, generate_sheet_id, used_sheet_id, total_used_serial):
        try:
            set_product_serial_code_list = SerialCode.objects.filter(sheet_id = generate_sheet_id).values_list('id', flat= True)
            
            if not len(total_used_serial) == 0 and len(set_product_serial_code_list) == len(total_used_serial):
                for i in range(len(set_product_serial_code_list)):
                    step1 = total_used_serial[i]
                    step2 = SerialCode.objects.filter(sheet_id = used_sheet_id,code__in = step1).values_list('id', flat= True)
                    
                    for id in list(step2):
                        SetSerialCodeComponent.objects.create(
                            set_serial_code_id = set_product_serial_code_list[i],
                            component_serial_code_id = id
                        )
        except Exception:
            raise Exception('생산 시리얼과 부품 시리얼을 연결하는중 오류가 발생했습니다.')
        
        
    @jwt_decoder
    def post(self, request):
        input_data = json.loads(request.body)
        user = request.user
        try:
            with transaction.atomic():
                # components 의 개수와 생산할 세트 품목의 개수가 같아야 한다.
                manufacture_quantity = input_data.get('manufacture_quantity')
                components = input_data.get('components')
                
                if not len(components) == int(manufacture_quantity):
                    return JsonResponse({'message' : '세트 생산에 필요한 구성품의 개수만큼 components가 들어오지 않았습니다.'}, status = 403)

                generate_sheet_id = self.generate_sheet(input_data, user)
                create_set_serial_code(input_data,generate_sheet_id)
                used_sheet_id, total_used_serial = self.used_sheet(input_data, user, generate_sheet_id)
                # serial_code
                self.bind_set_serial_code(generate_sheet_id, used_sheet_id, total_used_serial)

                # related_sheet
                self.bind_used_generate_sheet(generate_sheet_id, used_sheet_id)
            
            return JsonResponse({'message' : '세트 생산이 완료되었습니다.', 'generate_sheet_id' : generate_sheet_id}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '세트 생산이 실패했습니다.'}, status = 403)

# 이동평균법 수정

class ModifyMovingAverageMethodView(View):
    def post(self, request):
        custom_price = request.POST['custom_price']
        product_id  = request.POST['product_id']
        
        try:
            target = MovingAverageMethod.objects.get(product_id = product_id)
            target.custom_price = custom_price
            target.save()
            return JsonResponse({'message' : '수정 완료'}, status = 200)
        except Exception:
            return JsonResponse({'message' : '커스텀 가격을 수정하는데 애러가 발생'}, status = 403)

class InquireSheetLogView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id')

        log_id_list = SheetLog.objects.filter(sheet_id = sheet_id).values_list('id', flat= True)
        check = SheetLog.objects.filter(sheet_id = sheet_id)
        
        result = list(SheetCompositionLog.objects.filter(sheet_log_id__in = log_id_list).values(
            'id',
            'sheet_log__id',
            'sheet_log__sheet_id',
            'sheet_log__user_name',
            'sheet_log__type',
            'sheet_log__company',
            'sheet_log__date',
            'sheet_log__etc',
            'sheet_log__created_at',
            'sheet_log__timestamp',
            'product_id',
            'product__product_code',
            'product__product_group__name',
            'product__name',
            'unit_price',
            'quantity',
            'warehouse_code',
            'location',
            'etc'
        ))
        return JsonResponse({'message' : result}, status = 200)

class InquireSerialLogView(View):
    def get(self, request):
        serial_code = request.GET.get('serial_code')

        sheet_id_list = list(SerialCode.objects.filter(code = serial_code).values_list('sheet_id', flat= True))

        sheets = Sheet.objects.filter(id__in = sheet_id_list)

        result = []

        for sheet in sheets:
            if  sheet.date.year == sheet.created_at.year and \
                sheet.date.month == sheet.created_at.month and \
                sheet.date.day == sheet.created_at.day:    
                dict = {
                    'date'    : sheet.date,
                    'time'    : f'{sheet.created_at.hour}:{sheet.created_at.minute}',
                    'type'    : sheet.type,
                    'content' : sheet.id,
                    'user'    : sheet.user.name
                }
            else:
                dict = {
                    'date'    : sheet.date,
                    'time'    : "",
                    'type'    : sheet.type,
                    'content' : sheet.id,
                    'user'    : sheet.user.name
                }
            result.append(dict)

        serial_code_id = SerialCode.objects.filter(code = serial_code).last().id
        sheets_2 = SerialCodeValue.objects.filter(serial_code_id = serial_code_id)

        for sheet2 in sheets_2:
            
            dict = {
                'date'    : f'{sheet2.date.year}-{(str(sheet2.date.month).zfill(2))}-{(str(sheet2.date.day).zfill(2))}',
                'time'    : f'{sheet2.date.hour}:{str(sheet2.date.minute).zfill(2)}',
                'type'    : sheet2.title.title,
                'value_id': sheet2.id,
                'content' : sheet2.contents,
                'user'    : sheet2.user.name
            }
            result.append(dict)

        return JsonResponse({'message' : result}, status = 200)

class DecomposeSetSerialCodeView(View):
    def check_serials(self, serials):
        check_list = []
        try:
            for serial_code in serials:
                # 최종 히스토리
                last_history = SerialCode.objects.filter(code = serial_code).last()
                
                if Sheet.objects.get(id = last_history.sheet_id).type == 'outbound': 
                    raise KeyError
                
                serial_code_query_set = SerialCode.objects.filter(code = serial_code)
                
                for query in serial_code_query_set:
                    if Sheet.objects.get(id = query.sheet_id).type == 'generate':
                        sheet_id = query.sheet_id
                        check_list.append(sheet_id)
        except KeyError:
            return 'check_serial'
        
        # 중복 제거
        checked_list = []
        for value in check_list:
            if value not in checked_list:
                checked_list.append(value)
        
        if not len(checked_list) == 1:
            raise Exception("serials의 값을 확인해주세요.")
        
        targert_sheet_id = checked_list[0]

        return targert_sheet_id

    def generate_sheet_2(self, set_product_id, generate_sheet_id, LAB, warehouse_code):
        try:           
            set_product  = Product.objects.get(id = set_product_id)
        except Product.DoesNotExist:
            return JsonResponse({'message' : f'제품 ID:{set_product_id}는 존재하지 않습니다.'}, status = 403) 

        if set_product.is_set == False:
            return JsonResponse({'message' : f'이 상품은 세트가 아닙니다. 생산 불가능 합니다.'}, status = 403) 
        ### 이동 평균법으로 가격을 가져오자.

        component_list = ProductComposition.objects.filter(set_product_id = set_product_id).values_list('composition_product_id', flat= True) 
                
        generate_set_product_price = 0
        for component_id in component_list:
            mam_price = MovingAverageMethod.objects.get(product_id = component_id)
            
            
            # 수량만큼 추가로 계산
            quantity_2 = ProductComposition.objects.get(set_product_id = set_product.id, composition_product_id = component_id).quantity
            if mam_price.custom_price == 0:
                target_price = mam_price.average_price * quantity_2
            else:
                target_price = mam_price.custom_price * quantity_2
            generate_set_product_price += target_price
        
    
        labor_price = set_product.labor
        total_price = generate_set_product_price + labor_price 


        generate_sheet_composition = SheetComposition.objects.create(
            sheet_id        = generate_sheet_id,
            product_id      = set_product.id,
            quantity        = LAB, 
            unit_price      = total_price,
            etc             = f'세트를 생산했습니다.{generate_sheet_id}'
        )
        
        # 수량 반영
        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = set_product.id)
                
        if stock.exists():
            before_quantity = stock.last().stock_quantity
            stock_quantity  = before_quantity + int(LAB)
        else:
            stock_quantity  = int(LAB)

        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = set_product.id).create(
            sheet_id = generate_sheet_id,
            stock_quantity = stock_quantity,
            product_id = set_product.id,
            warehouse_code = warehouse_code )
        
        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = set_product.id).update_or_create(
            product_id = set_product.id,
            warehouse_code = warehouse_code,
            defaults={'total_quantity' : stock_quantity})
        
        # mam_create_sheet(set_product.id, total_price, int(LAB), stock_quantity)
        

        

    def used_sheet_2(self, used_sheet_id, set_product_id, LAB, warehouse_code):
        try:
            product_component = ProductComposition.objects.filter(set_product_id = set_product_id)

            components = []

            for i in range(LAB):
                component = []
                for product in product_component:
                    form = {
                        "product_code" : product.composition_product.product_code,
                        "quantity"     : product.quantity,
                    }
                    component.append(form)  
                components.append(component)

            for component in components:
                for check_product in  component:
                    check_product_id = Product.objects.get(product_code = check_product.get('product_code')).id
                    try:
                        check_price = MovingAverageMethod.objects.get(product_id = check_product_id)

                        if check_price.custom_price == 0:
                            unit_price = check_price.average_price
                        else:
                            unit_price = check_price.custom_price
                    except MovingAverageMethod.DoesNotExist:
                        unit_price = 0

                    SheetComposition.objects.create(
                        sheet_id        = used_sheet_id,
                        product_id      = check_product_id,
                        quantity        = check_product.get('quantity'), 
                        unit_price      = unit_price,
                        etc             = '세트 생산으로 인한 소진'
                    )
                
                    # 수량 반영
                    stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = check_product_id)
                
                    if stock.exists():
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity - int(check_product.get('quantity'))
                    else:
                        stock_quantity  = int(check_product.get('quantity'))

                    StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = check_product_id).create(
                        sheet_id = used_sheet_id,
                        stock_quantity = stock_quantity,
                        product_id = check_product_id,
                        warehouse_code = warehouse_code )
                    
                    QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = check_product_id).update_or_create(
                        product_id = check_product_id,
                        warehouse_code = warehouse_code,
                        defaults={'total_quantity' : stock_quantity})
        except Exception:
            raise Exception({'message' : 'used_sheet를 생성하는중 에러가 발생했습니다.'})
                
    @jwt_decoder
    def post(self, request):
        user = request.user
        input_data = json.loads(request.body)
        serials = input_data.get('serials')
        try:
            with transaction.atomic():
                generate_sheet_id = self.check_serials(serials)
                # 시리얼 체크 결과 값으로 메세지 날리기.
                if generate_sheet_id == 'check_serial':
                    return JsonResponse({'message' : f'들어온 시리얼 코드에 문제가 있습니다.', 'failed_serial' : serials }, status = 403)
                target_query = SheetComposition.objects.get(sheet_id = generate_sheet_id)
                # 옵션
                set_product_id = target_query.product_id
                manufacture_quantity = target_query.quantity
                warehouse_code = target_query.warehouse_code
                LAB = manufacture_quantity - len(serials)
                serial_quantity2 = len(serials)
                
                # 로그 찍기
                used_sheet_id = Sheet.objects.get(id = generate_sheet_id).related_sheet_id
                generate_sheet_log = create_sheet_logs(generate_sheet_id, user)
                used_sheet_log     = create_sheet_logs(used_sheet_id, user)

                
                # 롤백
                rollback_sheet_detail(generate_sheet_id)
                SheetComposition.objects.filter(sheet_id = generate_sheet_id).delete()
                self.generate_sheet_2(set_product_id, generate_sheet_id, LAB, warehouse_code)
                
                
                for serial_code in serials:
                    set_serial_code = SerialCode.objects.get(sheet_id = generate_sheet_id, code = serial_code)
                    bind_list = SetSerialCodeComponent.objects.filter(set_serial_code_id = set_serial_code.id).values_list('component_serial_code', flat = True)
                    SerialCode.objects.filter(sheet_id = used_sheet_id, id__in = bind_list).delete()
                    set_serial_code.delete()
                rollback_sheet_detail(used_sheet_id)
                SheetComposition.objects.filter(sheet_id = used_sheet_id).delete()
                self.used_sheet_2(used_sheet_id, set_product_id, LAB, warehouse_code)

                # 작성자 수정
                UPDATED_USER = Sheet.objects.filter(id = generate_sheet_id).update(user_id = user.id)

            
            return JsonResponse({'message' : '입력하신 serials 를 해체 성공했습니다.'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '시리얼 코드 해체 시도 중 실패했습니다.'}, status = 403)

class DeleteMistakeSerialCodeView(View):
    @jwt_decoder
    def post(self, request):
        user = request.user
        input_data = json.loads(request.body)
        serials  = input_data.get('serials')
        sheet_id = input_data.get('sheet_id')
        warehouse_code = "A"

        # 시리얼 체크
        serial_code_id_list = []
        failed_serial_code = []
        
        for serial_code in serials:
            last_sheet_id = SerialCode.objects.filter(code = serial_code).latest('id').sheet_id
            
            if not last_sheet_id == sheet_id:
                dict_A = {}
                dict_A.update({'serial_code' : serial_code, 'sheet_id' : last_sheet_id })
                failed_serial_code.append(dict_A)

            serial_code_id = SerialCode.objects.get(sheet_id = sheet_id, code = serial_code).id
            serial_code_id_list.append(serial_code_id)
                

        if not len(failed_serial_code) == 0:
            return JsonResponse({'message': '환원에 실패했습니다.', 'failed_serial_code' : failed_serial_code}, status = 403)

        # 로그 찍히기 전에 error_serial_code가 있으면 return을 한다.
                
        try:
            with transaction.atomic():
                create_sheet_logs(sheet_id, user)
                UPDATED_USER = Sheet.objects.filter(id = sheet_id).update(user_id = user.id)

                if Sheet.objects.get(id = sheet_id).type == 'inbound':
                    
                    for serial_code_id in serial_code_id_list:
                        product_id = SerialCode.objects.get(id = serial_code_id).product_id
                        target_sheet = SheetComposition.objects.get(sheet_id = sheet_id, product_id = product_id)
                        before_quantity = target_sheet.quantity
                        target_sheet.quantity = before_quantity - 1
                        target_sheet.save()
                        delete_serial_code = SerialCode.objects.get(id = serial_code_id).delete()
                    
                        # 실제 수량 반영
                        target_product_before_quantity = QuantityByWarehouse.objects.get(product_id = product_id).total_quantity
                        # 시리얼 수량
                        target_product_after_quantity = target_product_before_quantity - 1
                        QuantityByWarehouse.objects.filter(product_id = product_id).update(total_quantity = target_product_after_quantity)
                        # stock_by_warehouse 수정
                        target_sbw_before_quanitty = StockByWarehouse.objects.filter(sheet_id = sheet_id, product_id = product_id).last().stock_quantity
                        target_sbw_after_quantity = target_sbw_before_quanitty - 1
                        StockByWarehouse.objects.create(
                            sheet_id = sheet_id,
                            stock_quantity = target_sbw_after_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code)

                if Sheet.objects.get(id = sheet_id).type == 'outbound':
                    for serial_code_id in serial_code_id_list:
                    
                        product_id = SerialCode.objects.get(id = serial_code_id).product_id
                        target_sheet = SheetComposition.objects.get(sheet_id = sheet_id, product_id = product_id)
                        before_quantity = target_sheet.quantity
                        target_sheet.quantity = before_quantity - 1
                        target_sheet.save()
                        delete_serial_code = SerialCode.objects.get(id = serial_code_id).delete()
                    
                        # 실제 수량 반영
                        target_product_before_quantity = QuantityByWarehouse.objects.get(product_id = product_id).total_quantity
                        # 시리얼 수량
                        target_product_after_quantity = target_product_before_quantity + 1
                        QuantityByWarehouse.objects.filter(product_id = product_id).update(total_quantity = target_product_after_quantity)
                        # stock_by_warehouse 수정
                        target_sbw_before_quanitty = StockByWarehouse.objects.filter(sheet_id = sheet_id, product_id = product_id).last().stock_quantity
                        target_sbw_after_quantity = target_sbw_before_quanitty + 1
                        StockByWarehouse.objects.create(
                            sheet_id = sheet_id,
                            stock_quantity = target_sbw_after_quantity,
                            product_id = product_id,
                            warehouse_code = warehouse_code)
                
            return JsonResponse({'message' : '시리얼 수량 수정이 완료되었습니다.'}, status = 200)
        except SerialCode.DoesNotExist:
            return JsonResponse({'message' : '입력하신 시리얼 정보를 확인해주세요.'}, status = 403)        
        except SheetComposition.DoesNotExist:
            return JsonResponse({'message' : '존재하지 않는 sheet의 세부 사항입니다.'}, status = 403)
        
class QueryTestView(View):
    def get(self, request):
        product_id = request.GET.get('product_id')
        
        get_product = Product.objects.get(id = product_id)
        
        check = get_product.movingaveragemethod__name
        return JsonResponse({'message' : check})
        