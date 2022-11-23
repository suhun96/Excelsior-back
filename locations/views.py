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
        property_list = list(WarehouseProperty.objects.all().values())

        return JsonResponse({'message' : property_list }, status = 200)
        
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

class WarehouseInfoView(View):
    def post(self, request):
        input_data = request.POST
        
        if not 'name' in input_data:
            return JsonResponse({'message' : '창고 이름을 입력해주세요.'}, status = 403)
        
        if not 'code' in input_data:
            return JsonResponse({'message' : '창고 코드를 입력해주세요.'}, status = 403)

        if not Warehouse.objects.filter(code = input_data['code']).exists():
            SET = {}
            for key, value in input_data.items():
                if key in ['name', 'code', 'type', 'way', 'etc']:
                    SET.update({key : value})

            obj, created = Warehouse.objects.update_or_create(
                code = input_data['code'],
                defaults={**SET})
            
            if created == False:
                return JsonResponse({'message' : '기존의 창고정보를 수정했습니다.'}, status = 200)
            else:
                return JsonResponse({'message' : '새로운 창고정보를 생성했습니다.'}, status = 200)            
        else:
            SET = {}
            for key, value in input_data.items():
                if key in ['name', 'code', 'type', 'way', 'etc']:
                    SET.update({key : value})

            obj, created = Warehouse.objects.update_or_create(
                code = input_data['code'],
                defaults={**SET})
            
            if created == False:
                return JsonResponse({'message' : '기존의 창고정보를 수정했습니다.'}, status = 200)
            else:
                return JsonResponse({'message' : '새로운 창고정보를 생성했습니다.'}, status = 200)            

    def get(self, request):
        warehouse_list = list(Warehouse.objects.all().values())

        return JsonResponse({'message' : warehouse_list}, status = 200)