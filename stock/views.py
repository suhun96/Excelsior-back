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

        try:
            with transaction.atomic():
                new_sheet = create_sheet(input_data, user)
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

                        stock = StockByWarehouse.objects.filter(warehouse_code = warehouse_code, product_id = product_id)
                        
                        if not stock.exists():
                            stock_quantity = 0

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
                        
                        # product_serial_generate
                        if Product.objects.get(id = product_id).is_serial == True:
                            create_product_serial_code(product_id, quantity, new_sheet_id)
                        else:
                            pass

                    register_checker(input_data)
                    telegram_bot(new_sheet_id)

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
                            stock_quantity = 0

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

                    telegram_bot(new_sheet_id)
                    
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

                update_options = ['company_id', 'etc', 'date']

                for key, value in modify_data.items():
                    if key in update_options:
                        UPDATE_SET.update({ key : value })

                Sheet.objects.filter(id = sheet_id).update(**UPDATE_SET)

                # 업데이트 날짜 적용
                tartget_sheet = Sheet.objects.get(id = sheet_id)
                tartget_sheet.updated_at = datetime.now()
                tartget_sheet.save()
                # 업데이트 문서 번호
                generate_document_num(tartget_sheet.id)
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
                rollback_sheet_detail(sheet_id)
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
        offset         = int(request.GET.get('offset'))
        limit          = int(request.GET.get('limit'))
        name           = request.GET.get('user_name', None)
        stock_type     = request.GET.get('type', None)
        date_start     = request.GET.get('date_start', None)
        date_end       = request.GET.get('date_end', None)
        company_name   = request.GET.get('company_name', None)
        stock_type     = request.GET.get('type', None)


        length = Sheet.objects.all().count()


        q = Q(date__range = (date_start, date_end))

        if stock_type:
            q &= Q(type__icontains = stock_type)
        if name:
            user_id = User.objects.get(name = name).id
            q &= Q(user_id__exact = user_id)
        if company_name:
            company_id = Company.objects.get(name = company_name).id
            q &= Q(company_id = company_id)

        
        sheets = Sheet.objects.filter(q).order_by('date')[offset : offset+limit]

        for_list = []
        
        for sheet in sheets:
            id           = sheet.id
            user_name    = User.objects.get(id = sheet.user.id).name
            stock_type   = sheet.type
            
            company = Company.objects.get(id = sheet.company_id)
            company_name = company.name
            company_id = company.id
            company_code = company.code
            

            etc          = sheet.etc
            date         = sheet.date

            year    = date.year
            month   = date.month
            month   = str(month).zfill(2)
            day     = date.day
            day     = str(day).zfill(2)
            
            dict = {
                'id'        :  id,       
                'type'      : stock_type,
                'user'      : user_name,
                'date'      : f"{year}-{month}-{day}",
                'company_id'    : company_id,
                'company_name'  : company_name,
                'company_code'  : company_code,
                'etc'       : etc,
                'created_at' : sheet.created_at,
                'updated_at' : sheet.updated_at
            }
            
            for_list.append(dict)


        return JsonResponse({'message' : for_list, 'length': length}, status = 200)

class InfoSheetListView(View):
    def get(self, request):

        length = SheetComposition.objects.all().count()
        
        # sheet
        sheet_id       = request.GET.get('sheet_id', None)
        name           = request.GET.get('user_name', None)
        stock_type     = request.GET.get('type', None)
        date_start     = request.GET.get('date_start', None)
        date_end       = request.GET.get('date_end', None)
        company_name   = request.GET.get('company_name', None)
        # sheet-detail 
        product_name   = request.GET.get('product_name', None)
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

            return JsonResponse({'message' : list(sheet_detail) , 'length': length}, status = 200)

        else:
            offset = int(request.GET.get('offset'))
            limit  = int(request.GET.get('limit'))

            if not date_start:
                return JsonResponse({'message' : "기준 시작 날짜 설정 오류"}, status = 403)
            if not date_end:
                return JsonResponse({'message' : "기준 종료 날짜 설정 오류"}, status = 403)
            
            # Sheet 필터링
            q = Q(sheet__date__range = (date_start, date_end))

            if name:
                user_id = User.objects.get(name = name).id
                q &= Q(sheet__user_id__exact = user_id)
            if stock_type:
                q &= Q(sheet__type = stock_type)
            if product_name:
                product_id = Product.objects.get(name = product_name).id
                q &= Q(product_id = product_id)
            if company_name:
                company_id = Company.objects.get(name = company_name).id
                q &= Q(sheet__company_id = company_id)
            if product_group_id:
                product_id_list = Product.objects.filter(product_group_id = product_group_id).values_list('id', flat = True)
                q &= Q(product_id__in = product_id_list)
            
            sheet_detail = SheetComposition.objects.filter(q)[offset : offset+limit].values(
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
            
        
            return JsonResponse({'message' : list(sheet_detail) , 'length': length}, status = 200)

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
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
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
                    'product_group_name'    : ProductGroup.objects.get(code = product.productgroup_code).name,
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
        if stock_type == "generate":
            stock_type = "생산"
        if stock_type == "new":
            stock_type = "초도 입고"

        document_num = f"{year}/{month}/{day}-{stock_type}-{sheet_id}"
    
        return document_num

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
                'company_name'          : Company.objects.get(id = sheet.company_id).name,
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
                'company_name'          : Company.objects.get(id = sheet.company_id).name,
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

        if process_type == "generate":
            set_product_code = request.GET.get('set_product_code', None)

            if not set_product_code:
                return JsonResponse({'message' : '생산 시리얼 코드 체크를 위해서는 set_product_code가 필요합니다.'}, status = 403)

            if not SerialCode.objects.filter(code = serial_code).exists(): 
                return JsonResponse({'message' : '존재하지 않는 시리얼 입니다.'}, status = 403)
            
            else:
                set_product_id = Product.objects.get(product_code = set_product_code).id
                component_ids = ProductComposition.objects.filter(set_product_id = set_product_id).values_list('composition_product', flat= True)
                
                target_product_id = SerialCode.objects.get(code = serial_code).product_id
                
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
    @jwt_decoder
    def post(self, request):
        user = request.user
        serial_code_title_id = request.POST['title_id']
        serial_code_id       = request.POST['serial_code_id']
        contents             = request.POST['contents']
        
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
                'product_name'      : product_info.name,
                'product_code'      : product_info.product_code,
                'WBQ'               : WBQ_dict,
                'total_quantity'    : total['total_quantity__sum'],
                'required_quantity' : ProductComposition.objects.get(set_product_id= set_proudct_info.id , composition_product_id = id).quantity
            }
            
            RESULT_LIST.append(conponents_dict)

        return JsonResponse({'message' : RESULT_LIST}, status = 200)

class GenerateSetProductView(View):
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

                generate_sheet_id = generate_sheet.id
                
                try:           
                    set_product   = Product.objects.get(product_code =set_product_code)
                except Product.DoesNotExist:
                    return JsonResponse({'message' : f'{set_product_code}는 존재하지 않습니다.'}, status = 403) 

                if set_product.is_set == False:
                    return JsonResponse({'message' : f'이 상품은 세트가 아닙니다. 생산 불가능 합니다.'}, status = 403) 
                
                generate_sheet_composition = SheetComposition.objects.create(
                    sheet_id        = generate_sheet.id,
                    product_id      = set_product.id,
                    quantity        = manufacture_quantity, 
                    warehouse_code  = warehouse_code,
                    unit_price      = 123456,
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
                
                used_sheet_id = used_sheet.id

                for component in components:
                    component_id = Product.objects.get(product_code = component.get('product_code')).id
                    SheetComposition.objects.create(
                        sheet_id        = used_sheet.id,
                        product_id      = component_id,
                        quantity        = component.get('quantity'), 
                        warehouse_code  = component.get('warehouse_code'),
                        unit_price      = 0,
                        etc             = '세트 생산으로 인한 소진'
                    )
                    # 시리얼 코드 체크
                    if 'serials' in component:
                        count_serial_code(input_data, component, used_sheet)
    
                    # 수량 반영
                    stock = StockByWarehouse.objects.filter(warehouse_code = component.get('warehouse_code'), product_id = component_id)
                
                    if stock.exists():
                        before_quantity = stock.last().stock_quantity
                        stock_quantity  = before_quantity - int(component.get('quantity'))
                    else:
                        stock_quantity  = int(component.get('quantity'))

                    StockByWarehouse.objects.filter(warehouse_code = component.get('warehouse_code'), product_id = component_id).create(
                        sheet_id = used_sheet.id,
                        stock_quantity = stock_quantity,
                        product_id = component_id,
                        warehouse_code = component.get('warehouse_code') )
                    
                    QuantityByWarehouse.objects.filter(warehouse_code = component.get('warehouse_code'), product_id = component_id).update_or_create(
                        product_id = component_id,
                        warehouse_code = component.get('warehouse_code'),
                        defaults={'total_quantity' : stock_quantity})

            return used_sheet_id
        except Exception:
            raise Exception({'message' : 'used_sheet를 생성하는중 에러가 발생했습니다.'})

    @jwt_decoder
    def post(self, request):
        input_data = json.loads(request.body)
        user = request.user
        # try:
        generate_sheet_id = self.generate_sheet(input_data, user)
        create_set_serial_code(input_data, generate_sheet_id)
        used_sheet_id = self.used_sheet(input_data, user, generate_sheet_id)

        #related_sheet
        generate_sheet = Sheet.objects.get(id = generate_sheet_id)
        generate_sheet.related_sheet_id = used_sheet_id
        used_sheet = Sheet.objects.get(id = used_sheet_id)
        used_sheet.related_sheet_id = generate_sheet_id
        generate_sheet.save()
        used_sheet.save()
        
        return JsonResponse({'message' : '세트 생산이 완료되었습니다.', 'generate_sheet_id' : generate_sheet_id}, status = 200)
        # except Exception:
        #     return JsonResponse({'message' : '세트 생산이 실패했습니다.'}, status = 403)
       