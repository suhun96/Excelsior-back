from django.shortcuts   import render
from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from locations.models   import *
# Create your views here.

class CreateWarehousePropertyView(View):
    def post(self, request):
        input_data = request.POST
        WarehouseProperty.objects.create(
            contents = input_data['contents']
        )

        return JsonResponse({'message' : '적치 속성 생성'}, status = 200)

    def get(self, request):
        list = list(WarehouseProperty.objects.filter().values())

        return JsonResponse({'message' : list }, status = 200)
        
class CreateWarehouseTypeView(View):
    def post(self, request):
        input_data = request.POST
        WarehouseType.objects.create(
            contents = input_data['contents']
        )

        return JsonResponse({'message' : '적치 타입 생성'}, status = 200)

    def get(self, request):
        list = list(WarehouseType.objects.filter().values())

        return JsonResponse({'message' : list }, status = 200)

class WarehouseInfoView(View):
    def post(self, request):
        input_data = request.POST

        if not 'name' in input_data:
            return JsonResponse({'message' : '창고 이름을 입력해주세요.'}, status = 403)
        
        if not 'code' in input_data:
            return JsonResponse({'message' : '창고 코드를 입력해주세요.'}, status = 403)

        if Warehouse.objects.filter(code = input_data['code']).exists():
            return JsonResponse({'message' : '창고 코드가 이미 존재합니다.'}, status = 403)

        CREATE_SET = {}
        CREATE_OPT = ['name', 'code', 'type', 'way', 'etc']

        for key, value in input_data.items():
            if key in CREATE_OPT:
                CREATE_SET.update({key : value})
            else:
                return JsonResponse({'message' : '존재하지 않는 키값입니다.'}, status = 403)
        new_warehouse = Warehouse.objects.create(**CREATE_SET)
        check_warehouse = list(Warehouse.objects.filter(id = new_warehouse.id).values())
        return JsonResponse({'message' : '창고 생성', '생성 내용': check_warehouse}, status = 200)

    def get(self, request):
        warehouse_list = list(Warehouse.objects.all().values())

        return JsonResponse({'message' : warehouse_list}, status = 200)