from django.shortcuts   import render
from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from locations.models   import *
from django.db.models   import Q , Sum

from users.decorator    import jwt_decoder

class CreateWarehousePropertyView(View):
    def post(self, request):
        input_data = request.POST
        WarehouseProperty.objects.create(
            contents = input_data['contents']
        )

        return JsonResponse({'message' : '적치 속성 생성'}, status = 200)

    def get(self, request):
        property_list = list(WarehouseProperty.objects.all().values())

        return JsonResponse({'message' : property_list }, status = 200)

class ModifyWarehousePropertyView(View):
    def post(self, request):
        warehouse_property_id = request.POST['id']
        modify_data = request.POST

        if WarehouseProperty.objects.filter(contents = modify_data['contents']).exists():
            return JsonResponse({'message' : '이미 존재하는 Property입니다.' }, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['contents']
                
                for key, value in modify_data.items():
                    if key == 'status':
                        if value == 'true':
                            value = True
                        elif value == 'false':
                            value = False
                        UPDATE_SET.update({key : value})

                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    
                WarehouseProperty.objects.filter(id = warehouse_property_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class DeleteWarehousePropertyView(View):
    def post(self, request):
        warehouse_property_id = request.POST['id']

        WarehouseProperty.objects.get(id = warehouse_property_id).delete()
        return JsonResponse({'message' : '삭제를 성공했습니다.'}, status = 200)

########################################################################################################
    
class CreateWarehouseTypeView(View):
    def post(self, request):
        input_data = request.POST
        WarehouseType.objects.create(
            contents = input_data['contents']
        )

        return JsonResponse({'message' : '적치 타입 생성'}, status = 200)

    def get(self, request):
        type_list = list(WarehouseType.objects.all().values())

        return JsonResponse({'message' : type_list }, status = 200)

class ModifyWarehouseTypeView(View):
    def post(self, request):
        warehouse_type_id = request.POST['id']
        modify_data = request.POST

        if WarehouseType.objects.filter(contents = modify_data['contents']).exists():
            return JsonResponse({'message' : '이미 존재하는 Property입니다.' }, status = 403)
        
        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['contents']
                
                for key, value in modify_data.items():
                    if key == 'status':
                        if value == 'true':
                            value = True
                        elif value == 'false':
                            value = False
                        UPDATE_SET.update({key : value})

                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    
                WarehouseType.objects.filter(id = warehouse_type_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class DeleteWarehouseTypeView(View):
    def post(self, request):
        warehouse_type_id = request.POST['id']

        WarehouseType.objects.get(id = warehouse_type_id).delete()
        return JsonResponse({'message' : '삭제를 성공했습니다.'}, status = 200)
    

class WarehouseInfoView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        
        if not 'name' in input_data:
            return JsonResponse({'message' : '창고 이름을 입력해주세요.'}, status = 403)
        
        if not 'code' in input_data:
            return JsonResponse({'message' : '창고 코드를 입력해주세요.'}, status = 403)

        if 'id' in input_data:
            SET = {}
            for key, value in input_data.items():
                if key in ['name', 'code', 'type', 'way', 'etc', 'status']:
                    SET.update({key : value})
            
            Warehouse.objects.filter(id = input_data['id']).update(**SET)
            return JsonResponse({'message' : '수정'}, status = 200)
        
        else:
            if Warehouse.objects.filter(code = input_data['code']).exists():
                return JsonResponse({'message' : '코드 중복'}, status = 403)
            
            SET = {}
            for key, value in input_data.items():
                if key in ['name', 'code', 'type', 'way', 'etc']:
                    SET.update({key : value})

            Warehouse.objects.create(**SET)
            return JsonResponse({'message' : '생성'}, status = 200)


    def get(self, request):
        offset = int(request.GET.get('offset'))
        limit  = int(request.GET.get('limit'))

        length = Warehouse.objects.all().count()

        name = request.GET.get('name', None)
        code = request.GET.get('code', None)
        status = request.GET.get('status', None)
        
        q = Q()
        if name:
            q &= Q(name__icontains = name)
        if code:
            q &= Q(code__icontains = code)
        if status:
            q &= Q(status = status)
    

        warehouse_list = list(Warehouse.objects.filter(q)[offset : offset+limit].values())

        return JsonResponse({'message' : warehouse_list, 'length': length}, status = 200)

class WarehouseStatusView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        user = request.user
        warehouse_id = input_data.get('warehouse_id', None)
        try:
            with transaction.atomic():

                if not warehouse_id:
                    return JsonResponse({'message' : "warehouse_id를 입력해주세요"}, status = 403)

                if user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)

                if input_data['status'] == "False":
                    Warehouse.objects.filter(id = warehouse_id).update( status = False)
                    return JsonResponse({'message' : '창고 상태 False'}, status = 200)
                
                if input_data['status'] == "True": 
                    Warehouse.objects.filter(id = warehouse_id).update( status = True)
                    return JsonResponse({'message' : '창고 상태 True'}, status = 200)

        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'}, status = 403)

class SetMainWarehouseView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        user = request.user
        warehouse_id = input_data.get('warehouse_id', None)

        try:
            with transaction.atomic():

                if not warehouse_id:
                   return JsonResponse({'message' : "warehouse_id를 입력해주세요"}, status = 403)

                if user.admin == False:
                    return JsonResponse({'message' : '당신은 권한이 없습니다. '}, status = 403)
                
                Warehouse.objects.filter().update(main = False)

                Warehouse.objects.filter(id = warehouse_id).update(main = True)
                
            return JsonResponse({'message' : 'main 창고를 변경했습니다.'}, status = 200)

        except Exception:
            return JsonResponse({'message' : '예외 사항이 발생해서 트랜잭션을 중지했습니다.'}, status = 403)