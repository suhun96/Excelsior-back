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


        obj, created = Warehouse.objects.update_or_create(
            name = input_data['name'],
            code = input_data['code'],
            defaults={
                'type' : input_data['type'],
                'way'  : input_data['way'],
                'etc' : input_data['etc']
            })
        
        if created == False:
            return JsonResponse({'message' : '기존의 창고정보를 수정했습니다.'}, status = 200)
        else:
            return JsonResponse({'message' : '새로운 창고정보를 생성했습니다.'}, status = 200)

    def get(self, request):
        warehouse_list = list(Warehouse.objects.all().values())

        return JsonResponse({'message' : warehouse_list}, status = 200)