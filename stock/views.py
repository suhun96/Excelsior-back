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


# deco
from users.decorator    import jwt_decoder
from products.utils     import telegram_bot
from .utils             import *

class CreateSheetView(View):
    @jwt_decoder
    def post(self, request):
        input_data = json.loads(request.body)
        user = request.user

        new_sheet = create_sheet(input_data, user)
        new_sheet_id = new_sheet.id

        try:
            with transaction.atomic():
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
                        unit_price     = composition.get('unit_price')

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
                        
                        # 여기서 계산한 총 수량과
                        mam_create_sheet(product_id, unit_price, quantity, stock_quantity)

                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                            product_id = product_id,
                            warehouse_code = warehouse_code,
                            defaults={'total_quantity' : stock_quantity})

                        

                    register_checker(input_data)
                    telegram_bot(new_sheet_id)

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
                            defaults={'total_quantity' : stock_quantity})
                        
                    register_checker(input_data)
                    telegram_bot(new_sheet_id)
                    
                    return JsonResponse({'message' : '출고 성공'}, status = 200)

                if new_sheet.type == 'generate':
                    generated_composition = SheetComposition.objects.get(sheet_id = new_sheet_id)

                    product_id     = generated_composition.product.id
                    warehouse_code = generated_composition.warehouse_code
                    quantity       = generated_composition.quantity


                    # 재고 있는지 확인
                    stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                    
                    if stock.exists():
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity + int(quantity)
                    else:
                        stock_quantity  = int(quantity)

                    # 창고별 입고, 출고 내역 업데이트 
                    StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).create(
                        sheet_id = new_sheet_id,
                        stock_quantity = stock_quantity,
                        product_id = product_id,
                        warehouse_code = warehouse_code )
                    
                    # 창고별 제품 총 수량
                    QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id).update_or_create(
                        product_id = product_id,
                        warehouse_code = warehouse_code,
                        defaults={
                            
                            'total_quantity' : stock_quantity,
                        })

                    # 소진 
                    used_sheet = Sheet.objects.create(
                        user_id = user,
                        type = 'used',
                        company_code = 'EX',
                        etc = f'Sheet_ID :{new_sheet_id} 세트 생산으로 인한 재고소진'
                    )

                    set_compositions = ProductComposition.objects.filter(set_product_id = product_id).values()

                    for composition in set_compositions:
                        SheetComposition.objects.create(
                            sheet_id        = used_sheet.id,
                            product_id      = composition['composition_product_id'],
                            unit_price      = 0,
                            quantity        = composition['quantity'],
                            warehouse_code  = warehouse_code,
                            location        = Product.objects.get(id = composition['composition_product_id']).location,
                            etc             = f'Sheet_ID : {new_sheet_id} 생산으로 인한 구성품 소진입니다.'
                        )

                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = composition['composition_product_id'])
                        
                        if stock.exists():
                            before_quantity = stock.last().stock_quantity
                            stock_quantity  = before_quantity - int(composition['quantity'])
                        else:
                            stock_quantity  = int(composition['quantity'])

                        StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = composition['composition_product_id']).create(
                            sheet_id = used_sheet.id,
                            stock_quantity = stock_quantity,
                            product_id = composition['composition_product_id'],
                            warehouse_code = warehouse_code )
                        
                        QuantityByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = composition['composition_product_id']).update_or_create(
                            product_id = composition['composition_product_id'],
                            warehouse_code = warehouse_code,
                            defaults={
                                'total_quantity' : stock_quantity
                            })
                    
                    # serial code 생선
                    create_serial_code(generated_composition, new_sheet_id)
                    serial_codes = SerialAction.objects.filter(create = new_sheet_id).values('serial')
                    serial_code_list = []
                    for serial_code in serial_codes:
                        serial_code_list.append(serial_code['serial'])
                    
                    return JsonResponse({'message' : '생산 성공', 'serial_list' : serial_code_list}, status = 200)
        except Exception:
            return JsonResponse({'message' : 'keyerror'}, status = 403)

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
        
        sheet_id = modify_data.get('sheet_id')
        try:
            with transaction.atomic():
                # sheet, sheet_detail log 작성
                create_sheet_logs(sheet_id, modify_user)
                # sheet_detail 롤백 [입고 = (-), 출고 = (+)]
                rollback_sheet_detail(sheet_id)
                # sheet_detail 삭제
                SheetComposition.objects.filter(sheet_id = sheet_id).delete()

                # sheet 수정    
                UPDATE_SET = {'user' : modify_user}

                update_options = ['company_code', 'etc', 'date']

                for key, value in modify_data.items():
                    if key in update_options:
                        UPDATE_SET.update({ key : value })

                Sheet.objects.filter(id = sheet_id).update(**UPDATE_SET)

                # 업데이트 날짜 적용
                tartget_sheet = Sheet.objects.get(id = sheet_id)
                tartget_sheet.updated_at = datetime.now()
                tartget_sheet.save()
                # 수정된 sheet_detail 생성
                modify_sheet_detail(sheet_id, modify_data['products'])
                # 수정된 sheet_detail 수량 반영
                reflecte_sheet_detail(sheet_id)
                # 수정된 가격 반영
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
                rollback_quantity(sheet_id)
                # Sheet_detail 삭제
                SheetComposition.objects.filter(sheet_id = sheet_id).delete()
                # type 변환
                Sheet.objects.filter(id = sheet_id).update(type = "delete")

                return JsonResponse({'message' : 'sheet 삭제 완료'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

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
        stock_type = request.GET.get('type', None)

        q = Q()
        if stock_type:
            q &= Q(type__icontains = stock_type)

        
        sheets = Sheet.objects.filter(q).values(
            'id',
            'user',
            'type',
            'company_code',
            'etc',
            'date'
            'created_at'
        ).order_by('date')

        for_list = []
        for sheet in sheets:
            id           = sheet['id']
            user_name    = User.objects.get(id = sheet['user']).name
            stock_type   = sheet['type']

            company_name = Company.objects.get(code = sheet['company_code']).name
            etc          = sheet['etc']
            created_at   = sheet['created_at']
            
            dict = {
                'id'        :  id,       
                'type'      : stock_type,
                'user'      : user_name,
                'created_at'    : created_at,
                'company_name'  : company_name,
                'etc'       : etc
            }
            
            for_list.append(dict)


        return JsonResponse({'message' : for_list}, status = 200)

class InfoSheetListView(View):
    def generate_document_num(self, sheet_id, date):
        year  = date.year
        month = date.month
        day   = date.day
        sheet = Sheet.objects.get(id = sheet_id)
        stock_type = sheet.type
        sheet_id   = sheet.id
        
        # 타입 변환기.
        if stock_type == 'inbound':
            stock_type = "입고"
        if stock_type == "outbound":
            stock_type = "출고"
        if stock_type == 'new':
                stock_type = '등록'

        document_num = f"{year}/{month}/{day}-{stock_type}-{sheet_id}"
    
        return document_num

    def get(self, request):
        name           = request.GET.get('user_name', None)
        stock_type     = request.GET.get('type', None)
        date_start     = request.GET.get('date_start', None)
        date_end       = request.GET.get('date_end', None)
        company_name   = request.GET.get('company_name', None)
        product_name   = request.GET.get('product_name')
        warehouse_name = request.GET.get('warehouse_name', None)
        
        if not date_start:
            return JsonResponse({'message' : "기준 시작 날짜 설정 오류"}, status = 403)
        if not date_end:
            return JsonResponse({'message' : "기준 종료 날짜 설정 오류"}, status = 403)
        
        # Sheet 필터링
        q = Q(created_at__range = (date_start, date_end))

        if stock_type:
            q &= Q(type__icontains = stock_type)
        if name:
            user_id = User.objects.get(name = name).id
            q &= Q(user_id__exact = user_id)
        if company_name:
            company_code = Company.objects.get(name = company_name).code
            
            q &= Q(company_code = company_code)
        
        
        sheet_ids = Sheet.objects.filter(q).values_list('id', flat= True).order_by('date')

        for_list = []
        for sheet_id in sheet_ids:
            sheet = Sheet.objects.get(id = sheet_id)
            user_name    = User.objects.get(id = sheet.user.id).name
            stock_type   = sheet.type

            document_num = self.generate_document_num(sheet.id, sheet.date)
            sheet_company_name = Company.objects.get(code = sheet.company_code).name
            sheet_company_code = Company.objects.get(code = sheet.company_code).code
            
            etc          = sheet.etc
            created_at   = sheet.created_at
            
            # Sheet composition(detail) 필터링
            q2 = Q(sheet_id = sheet_id)
            
            if warehouse_name:
                warehouse_code = Warehouse.objects.get(name = warehouse_name).code
                q2 &= Q(warehouse_code__icontains = warehouse_code)
            if product_name:
                product_id = Product.objects.get(name = product_name).id
                q2 &= Q(product_id = product_id)


            compositions = SheetComposition.objects.filter(q2)
            
            for composition in compositions:
                product = Product.objects.get(id = composition.product_id)
                
                try: 
                    total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))
                except QuantityByWarehouse.DoesNotExist:
                    total = 0
                
                try:  
                    partial_quantity = QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                except QuantityByWarehouse.DoesNotExist:
                    partial_quantity = 0

                serial_codes = SerialCode.objects.filter(sheet_id = sheet_id, product_id = product.id).values_list('code', flat=True)
                
                list_serial_code = []

                for object in serial_codes:
                    list_serial_code.append(object)

                year    = sheet.date.year
                month   = sheet.date.month
                day     = sheet.date.day



                if product.company_code == "" :
                    dict = {
                        'sheet_id'              : sheet_id,
                        'document_num'          : document_num,
                        'user_name'             : user_name,
                        'type'                  : stock_type,
                        'company_name'          : sheet_company_name,
                        'company_code'          : sheet_company_code,
                        'etc'                   : etc,
                        'date'                  : f"{year}-{month}-{day}",
                        'product_code'          : product.product_code,
                        'product_name'          : product.name,
                        'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                        'barcode'               : product.barcode,
                        'price'                 : composition.unit_price,
                        'quantity'              : composition.quantity,
                        'total_quantity'        : total['total_quantity__sum'],
                        'warehouse_code'        : composition.warehouse_code,
                        'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                        'partial_quantity'      : partial_quantity,
                        'location'              : composition.location,
                        'serial_codes'          : list_serial_code,
                        'detail_etc'            : composition.etc   
                    }
                    for_list.append(dict) 
                
                else:
                    dict = {
                        'sheet_id'              : sheet_id,
                        'document_num'          : document_num,
                        'user_name'             : user_name,
                        'type'                  : stock_type,
                        'company_name'          : sheet_company_name,
                        'company_code'          : sheet_company_code,
                        'etc'                   : etc,
                        'date'                  : f"{year}-{month}-{day}",
                        'product_code'          : product.product_code,
                        'product_name'          : product.name,
                        'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                        'barcode'               : product.barcode,
                        'price'            : composition.unit_price,
                        'quantity'              : composition.quantity,
                        'total_quantity'        : total['total_quantity__sum'],
                        'warehouse_code'        : composition.warehouse_code,
                        'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                        'partial_quantity'      : partial_quantity,
                        'location'              : composition.location,
                        'serial_codes'          : list_serial_code,
                        'detail_etc'            : composition.etc   
                    }
                    for_list.append(dict)


        return JsonResponse({'message' : for_list}, status = 200)

class ClickSheetView(View):
    def get(self, request):
        sheet_id = request.GET.get('sheet_id', None)

        if not sheet_id:
            return JsonResponse({'message' : 'sheet id 가 입력되지 않았습니다.'}, status = 200)

        compositions = SheetComposition.objects.filter(sheet_id = sheet_id)

        for_list = []
        for composition in compositions:
            product = Product.objects.get(id = composition.product_id)
            total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))

            serial_codes = SerialCode.objects.filter(sheet_id = sheet_id ,product_id = product.id).values('code')
            list_serial_code = []
            
            for obj in serial_codes:
                list_serial_code.append(obj.get('code'))
            
            if product.company_code == "" :
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'barcode'               : product.barcode,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_code'        : composition.warehouse_code,
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list_serial_code,
                    'etc'                   : composition.etc   
                } 
            else:
                dict = {
                    'product_code'          : product.product_code,
                    'product_name'          : product.name,
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                    'barcode'               : product.barcode,
                    'company_name'          : Company.objects.get(code = product.company_code).name,
                    'unit_price'            : composition.unit_price,
                    'quantity'              : composition.quantity,
                    'total_quantity'        : total['total_quantity__sum'],
                    'warehouse_code'        : composition.warehouse_code,
                    'warehouse_name'        : Warehouse.objects.get(code = composition.warehouse_code).name,
                    'partial_quantity'      : QuantityByWarehouse.objects.get(warehouse_code = composition.warehouse_code, product_id = product.id).total_quantity,
                    'location'              : composition.location,
                    'serial_codes'          : list_serial_code,
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
                dict = {
                    'product_code' : get_product.product_code,
                    'product_name' : get_product.name,
                    'warehouse_code' : obj.warehouse_code,
                    'warehouse_name' : Warehouse.objects.get(code = obj.warehouse_code).name,
                    'status'       : get_product.status,
                    'safe_quantity': get_product.safe_quantity,
                    'quantity'     : obj.total_quantity,
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
                dict = {
                    'product_code' : get_product.product_code,
                    'product_name' : get_product.name,
                    'status'       : get_product.status,
                    'safe_quantity': get_product.safe_quantity,
                    'quantity'     : check['quantity'],
                    'ketword'      : get_product.keyword
                }
                result_list.append(dict) 
            return JsonResponse({'message': result_list})

class PriceCheckView(View):
    def post(self, request):
        input_data = request.POST
        
        try:
            company_code = input_data['company_code']
            product_id   = Product.objects.get(product_code = input_data['product_code']).id
            print(product_id)
            type         = input_data['type']
            
            if type == 'inbound':
                price = ProductPrice.objects.get(company_code = company_code, product_id = product_id).inbound_price
            
            if type == 'outbound':
                price = ProductPrice.objects.get(company_code = company_code, product_id = product_id).outbound_price
        
            return JsonResponse({'message' : f'{price}'}, status = 200)
        
        
        except Product.DoesNotExist:    
            return JsonResponse({'message' : '잘못된 요청을 보내셨습니다.2'}, status = 403)
        except ProductPrice.DoesNotExist:
            return JsonResponse({'message' : '0' }, status = 200)
        
class SerialCodeCheckView(View):
    def generate_document_num(self, sheet_id, created_at):
        year  = created_at.year
        month = created_at.month
        day   = created_at.day
        sheet = Sheet.objects.get(id = sheet_id)
        stock_type = sheet.type
        sheet_id   = sheet.id
        
        # 타입 변환기.
        if stock_type == 'inbound':
            stock_type = "입고"
        if stock_type == "outbound":
            stock_type = "출고"

        document_num = f"{year}/{month}/{day}-{stock_type}-{sheet_id}"
    
        return document_num

    def serial_product_code_checker(self, serial_code):
        product_id = SerialCode.objects.get(serial = serial_code).product_id

        product_code = Product.objects.get(id = product_id).product_code
        return product_code

    def serial_tracker(self, serial_code):
        sheet_id = SerialCode.objects.get(code = serial_code).sheet_id

        sheet = Sheet.objects.get(id = sheet_id )

        return sheet

    def print_sheet(self, sheet, serial_code):
        product_id = SerialCode.objects.get(code = serial_code).product_id
        
        sheet_composition = SheetComposition.objects.get(sheet_id = sheet.id , product_id = product_id)
        
        product = Product.objects.get(id = product_id)

        try: 
            total = QuantityByWarehouse.objects.filter(product_id = product.id).aggregate(Sum('total_quantity'))
      
            partial_quantity = QuantityByWarehouse.objects.get(warehouse_code = sheet_composition.warehouse_code, product_id = product.id).total_quantity,
        
        except QuantityByWarehouse.DoesNotExist:
            partial_quantity = 0
        except QuantityByWarehouse.DoesNotExist:
            total = 0

        document_num = self.generate_document_num(sheet.id, sheet.created_at)

        if product.company_code == "" :
            result = {
                'document_num'          : document_num,
                'user_name'             : sheet.user.name,
                'type'                  : sheet.type,
                'company_name'          : Company.objects.get(code = sheet.company_code).name,
                'etc'                   : sheet.etc,
                'created_at'            : sheet.created_at,
                'product_code'          : product.product_code,
                'product_name'          : product.name,
                'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                'barcode'               : product.barcode,
                'unit_price'            : sheet_composition.unit_price,
                'quantity'              : sheet_composition.quantity,
                'total_quantity'        : total['total_quantity__sum'],
                'warehouse_name'        : Warehouse.objects.get(code = sheet_composition.warehouse_code).name,
                'partial_quantity'      : partial_quantity,
                'location'              : sheet_composition.location,
                'etc'                   : sheet_composition.etc   
                } 
        else:
            result = {
                'document_num'          : document_num,
                'user'                  : sheet.user.name,
                'type'                  : sheet.type,
                'company_name'          : Company.objects.get(code = sheet.company_code).name,
                'etc'                   : sheet.etc,
                'product_code'          : product.product_code,
                'product_name'          : product.name,
                'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
                'barcode'               : product.barcode,
                'company_name'          : Company.objects.get(code = product.company_code).name,
                'unit_price'            : sheet_composition.unit_price,
                'quantity'              : sheet_composition.quantity,
                'total_quantity'        : total['total_quantity__sum'],
                'warehouse_name'        : Warehouse.objects.get(code = sheet_composition.warehouse_code).name,
                'partial_quantity'      : partial_quantity,
                'location'              : sheet_composition.location,
                'etc'                   : sheet_composition.etc   
            }
        
        return result

    def get(self, request):
        serial_code  = request.GET.get('serial_code')
        process_type = request.GET.get('process_type')

        
        if process_type == 'inbound':
            if not SerialCode.objects.filter(code = serial_code).exists():
                return JsonResponse({'message' : '입고 처리가 가능합니다.'}, status = 200)
            
            else:
                sheet = self.serial_tracker(serial_code)
                sheet_type  = sheet.type
                
                if sheet_type == 'inbound':
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '보유하고 있는 시리얼 입니다.', 'result': result}, status = 403)

                if sheet_type == 'create':
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '보유하고 있는 시리얼 입니다.', 'result': result}, status = 403)
        
                else:
                    return JsonResponse({'message' : '입고 처리가 가능합니다.'}, status = 200)

        if process_type == 'outbound':
            if not SerialCode.objects.filter(serial = serial_code).exists():
                return JsonResponse({'message' : '존재하지 않는 시리얼입니다.'}, status = 403)

            else:
                sheet = self.serial_tracker(serial_code)
                sheet_type  = sheet.type

                if sheet_type == "inbound":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.' , 'product_code' : product_code}, status = 200)

                if sheet_type == "create":
                    product_code = self.serial_product_code_checker(serial_code)
                    return JsonResponse({'message' : '출고 처리가 가능합니다.', 'product_code' : product_code}, status = 200)

                if sheet_type == "outbound":
                    result = self.print_sheet(sheet, serial_code)
                    return JsonResponse({'message': '이미 출고된 시리얼 입니다.', 'result': result }, status = 403)

class StockTotalView(View):
    def get(self, request):
        product_name    = request.GET.get('product_name', None)
        product_code    = request.GET.get('product_code', None)
        keyword         = request.GET.get('keyword', None)
        barcode         = request.GET.get('barcode', None)
        
        type            = request.GET.get('type', None)
        company_code    = request.GET.get('company_code', None)

        warehouse_code  = request.GET.get('warehouse_code', None)

        q = Q()
        if product_name:
            q &= Q(name__icontains = product_name)
        if product_code:
            q &= Q(product_code__icontains = product_code)
        if barcode:
            q &= Q(barcode__icontains = barcode)
        if keyword:
            q &= Q(keyword__icontains = keyword)

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
                    if not company_code:
                        price = 0
                    else:
                        check_price = ProductPrice.objects.get(company_code = company_code, product_id = product.id)
                        price = check_price.inbound_price

                if type == 'outbound':
                    if not company_code:
                        price = 0
                    else:
                        check_price = ProductPrice.objects.get(company_code = company_code, product_id = product.id)
                        price = check_price.outbound_price
                
                if not warehouse_code:
                    try:
                        partial_quantity = QuantityByWarehouse.objects.get(product_id = product.id, warehouse_code = product.warehouse_code).total_quantity
                    except QuantityByWarehouse.DoesNotExist:
                        partial_quantity = 0
                    dict = {
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

        for key, value in request.POST.item():
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
        
        Title_list = list(SerialCodeTitle.objects.filter(status = True).values())

        return JsonResponse({'message': Title_list})

# Serial Code - Value
class CreateSerialCodeValueView(View):
    def post(self, request):
        serial_code_title_id = request.POST['title_id']
        serial_code_id       = request.POST['serial_code_id']
        contents             = request.POST['contents']
        
        try:
            with transaction.atomic():
                obj, check = SerialCodeValue.objects.update_or_create(
                    title_id       = serial_code_title_id,
                    serial_code_id = serial_code_id,
                    defaults= {
                        'contents' : contents
                    })
                if check == True:
                    return JsonResponse({'message' : '생성 성공'}, status = 200)
                else:
                    return JsonResponse({'message' : '수정 성공'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : '잘못된 key 값을 입력하셨습니다.'}, status = 403)

### 완성 못시킨 코드 ###
class InquireSerialCodeValueView(View):
    def get(self, request):
        serial_code_ids = SerialCode.objects.all().values_list('id', flat= True)

        list_A = []

        for id in serial_code_ids:
            things = SerialCodeValue.objects.filter(serial_code_id = id)
            
            dict_A = {thing.serial_code : dict_B}
            
            for thing in things:
                dict_A.update({
                    'title' : things.title.title,
                    'contents' : things.contents
                })
                list_A.append(dict_A)

        return JsonResponse({'message': list_A})

# 평균가액

# class InquireS