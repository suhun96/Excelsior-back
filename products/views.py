import json, re

from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction, connection, IntegrityError
from django.db.models   import Q


# Model
from users.models       import *
from products.models    import *
from companies.models   import *
from locations.models   import *

# decorator & utills 
from users.decorator    import jwt_decoder, check_status
from products.utils     import *

class ProductGroupView(View):
    def get(self, request):
        name = request.GET.get('name')
        code = request.GET.get('code')
        
        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if code:
                q &= Q(code__icontains = code)
            
            result = list(ProductGroup.objects.filter(q).values())
        
            return JsonResponse({'message' : result}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
   
    def post(self, request):
        input_data = request.POST

        
        if not "name" in input_data:
            return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

        if ProductGroup.objects.filter(name = input_data['name']).exists():
                return JsonResponse({'message' : 'The product name is already registered.'}, status = 403)

        if ProductGroup.objects.filter(code = input_data['code']).exists():
                return JsonResponse({'message' : 'The product code is already registered.'}, status = 403)     
        
        

        REGEX_CODE = '[A-Z]{2}'  

        CREATE_SET = {}
        CREATE_OPT = ['name', 'code', 'etc']
        # create_options 로 request.POST 의 키값이 정확한지 확인.
        for key in dict(request.POST).keys():
            if key in CREATE_OPT:
                if key == 'code':
                    if not re.fullmatch(REGEX_CODE, input_data['code']):
                        return JsonResponse({'message' : '제품 그룹 코드의 형식을 확인해주세요. [A-Z] 2자리 '}, status = 403)

                CREATE_SET.update({ key : request.POST[key] })
            
            else:
                return JsonResponse({'message' : '잘못된 키값이 들어오고 있습니다.'}, status = 403)

        new_product_group = ProductGroup.objects.create(**CREATE_SET)

        check_PG = list(ProductGroup.objects.filter(id = new_product_group.id).values(
            'id',
            'name',
            'code',
            'etc',
            'status'
        ))

        return JsonResponse({'message' : check_PG}, status = 200)

class ModifyProductGroupView(View):
    def post(self, request):
        input_data = request.POST
        group_id = request.GET.get('group_id')

        if not ProductGroup.objects.filter(id = group_id).exists():
            return JsonResponse({'message' : '존재하지 않는 제품그룹입니다.'}, status = 403)

        try:
            with transaction.atomic():
                UPDATE_SET = {}

                update_options = ['name', 'etc']

                for key, value in input_data.items():
                    if key in update_options:
                        UPDATE_SET.update({ key : value })
                    
                ProductGroup.objects.filter(id = group_id).update(**UPDATE_SET)
                return JsonResponse({'message' : '업데이트 내역을 확인해 주세요~!!'}, status = 200)
        except:
            return JsonResponse({'message' : "예외 사항이 발생했습니다."}, status = 403)

class ProductInfoView(View):
    def get(self, request):
        keyword = request.GET.get('keyword', None)
        name = request.GET.get('name', None)
        productgroup_code = request.GET.get('product_group_code', None)
        warehouse_code = request.GET.get('warehouse_code', None)

        try:
            q = Q()
            if name:
                q &= Q(name__icontains = name)
            if keyword:
                q &= Q(search_word__icontains = keyword)
            if productgroup_code:
                q &= Q(productgroup_code__icontains = productgroup_code)
            if warehouse_code:
                q &= Q(warehouse_icontains = warehouse_code)
            
            result = list(Product.objects.filter(q).values())
        
            return JsonResponse({'message' : result}, status = 200)
        except:
            return JsonResponse({'message' : '예외 상황 발생'}, status = 403)
    
    def post(self, request):
        input_data = json.loads(request.body)
        
        name = input_data.get('name', None)
        product_group_code = input_data.get('product_group_code', None)
        warehouse_code = input_data.get('warehouse_code', None)
        company_code = input_data.get('company_code', None)
        is_set = input_data.get('is_set', None)
        compositions = input_data.get('compositions', None )
        
        # 필수값 제품명 확인
        if name == None:
            return JsonResponse({'message' : '제품명을 입력해주세요'}, status = 403)

        if product_group_code == None:
            return JsonResponse({'message' : '제품 코드를 입력해주세요'}, status = 403)
        else:
            if not ProductGroup.objects.filter(code = product_group_code).exists():
                return JsonResponse({'message' : '존재하지 않는 제품그룹 코드입니다.'}, status = 403)
        
        if warehouse_code:
            if not Warehouse.objects.filter(code = input_data['warehouse_code']).exists():
                return JsonResponse({'message' : '존재하지 않는 창고 코드입니다.'}, status = 403)
        try:
            with transaction.atomic():
                # 회사코드가 있으면
                if company_code:
                # 회사코드 체크
                    if not Company.objects.filter(code = company_code).exists():
                        return JsonResponse({'message' : f'[{company_code}] 존재하지 않는 회사 코드입니다.'})
                    
                    product = Product.objects.filter(productgroup_code = product_group_code) 

                    if product.exists():
                        productgroup_num = product.latest('created_at').product_num
                        change_int_num = int(productgroup_num) + 1
                        product_num = str(change_int_num).zfill(3)           
                    else:
                        product_num = '001'
                    
                    # 세트 상품이면 
                    if is_set == 1:
                        CREATE_SET = {
                            'is_set' : True,  
                            'productgroup_code' : product_group_code , 
                            'company_code' : company_code, 
                            'name' : name,
                            'product_num' : product_num
                        }
                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['safe_quantity', 'keyword', 'warehouse_code', 'location']:
                                CREATE_SET.update({key : value})
                        
                        # 새로운  세트 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)

                        # 새로운 세트 제품의 구성품 등록
                        for id, quantity in compositions.items():
                            ProductComposition.objects.create(
                                set_product_id = new_product.id,
                                composition_product_id = id,
                                quantity = quantity
                            )
                        return JsonResponse({'message' : '[Case 1] 새로운 세트 상품이 등록되었습니다.'}, status = 200) 
                    # 일반 상품이면
                    else:
                        CREATE_SET = {
                            'is_set' : False,  
                            'productgroup_code' : product_group_code , 
                            'company_code' : company_code, 
                            'name' : name,
                            'product_num' : product_num
                        }

                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['safe_quantity', 'keyword', 'warehouse_code', 'location']:
                                CREATE_SET.update({key : value})
                        
                        # 새로운 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)
                        
                        return JsonResponse({'message' : '[Case 2] 새로운 일반 상품이 등록되었습니다'}, status = 200) 
                    
                # 회사코드가 없으면 
                if not company_code:
                    product = Product.objects.filter(productgroup_code = product_group_code) 

                    if product.exists():
                        productgroup_num = product.latest('created_at').product_num
                        change_int_num = int(productgroup_num) + 1
                        product_num = str(change_int_num).zfill(3)           
                    else:
                        product_num = '001'
                    
                    # 세트 상품이면 
                    if is_set == 1:
                        CREATE_SET = {
                            'is_set' : True,  
                            'productgroup_code' : product_group_code ,  
                            'name' : name,
                            'product_num' : product_num
                        }
                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['safe_quantity', 'keyword', 'warehouse_code', 'location']:
                                CREATE_SET.update({key : value})
                        
                        # 새로운  세트 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)

                        # 새로운 세트 제품의 구성품 등록
                        for id, quantity in compositions.items():
                            ProductComposition.objects.create(
                                set_product_id = new_product.id,
                                composition_product_id = id,
                                quantity = quantity
                            )
                        return JsonResponse({'message' : '[Case 3] 새로운 세트 상품이 등록되었습니다.'}, status = 200) 
                    # 일반 상품이면
                    else:
                        CREATE_SET = {
                            'is_set' : False,  
                            'productgroup_code' : product_group_code ,  
                            'name' : name,
                            'product_num' : product_num
                        }

                        # 들어온 기타 정보사항 CREATE_SET에 추가
                        for key, value in input_data.items():
                            if key in ['safe_quantity', 'keyword', 'warehouse_code', 'location']:
                                CREATE_SET.update({key : value})
                        
                        # 새로운 제품 등록
                        new_product = Product.objects.create(**CREATE_SET)
                        
                        return JsonResponse({'message' : '[Case 4] 새로운 세트 상품이 등록되었습니다.'}, status = 200)
        
        except IntegrityError:
            return JsonResponse({'message' : 'compositions에 입력된 id 값을 확인해주세요'}, status = 403)

class ModifyProductInfoView(View):
    def post(self, request):
        input_data = request.POST
        product_id = input_data.get('id', None)
        
        if not product_id:
            return JsonResponse({'message' : "수정할 Product id가 입력되지 않았습니다."}, status = 403)
        if Product.objects.filter(id = product_id).exists() == False:
            return JsonResponse({'message' : "존재하지 않는 제품입니다."}, status = 403)
        
        UPDATE_SET = {}
        UPDATE_OPT = ['safe_quantity', 'keyword', 'name', 'location']

        try:
            with transaction.atomic():

                for key, value in input_data.items():
                    if key == 'warehouse_code':
                        if not Warehouse.objects.filter(code = value).exists():
                            return JsonResponse({'message' : '존재하지 않는 창고 코드입니다.'}, status = 403)
                        UPDATE_SET.update({key : value})

                    if key in UPDATE_OPT:
                        UPDATE_SET.update({key : value})
                
                Product.objects.filter(id = product_id).update(**UPDATE_SET)

                return JsonResponse({'message' : 'Check update'}, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KeyError'}, status = 403)
        except:
            return JsonResponse({'message' : '예외 사항 발생'}, status = 403)

class ProductEtcTitleView(View):
    def post(self, request):
        input_data = request.POST
        etc_title_id = input_data.get('etc_title_id', None)

        if not etc_title_id:
            return JsonResponse({'message': "수정에 필요한 비고란 제목 id값이 들어오지 않았습니다."}, status = 403)
        
        with transaction.atomic():
            UPDATE_SET = {}

            for key, value in input_data.items():
                if key == 'modify_title':
                    UPDATE_SET.update({'title' : value})
                if key == 'status':
                    if value == 'false':
                        UPDATE_SET.update({'status': False})
                    elif value == 'true':
                        UPDATE_SET.update({'status': True})

            ProductEtcTitle.objects.filter(id = etc_title_id).update(**UPDATE_SET)
            return JsonResponse({'message' : 'updated'}, status = 200)
        
            

    def get(self, request):
        # 권한 설정
        title_list = list(ProductEtcTitle.objects.all().values()) 

        return JsonResponse({'message' : title_list}, status = 200)

class ProductEtcDescView(View):
    def post(self, request):
        input_data = request.POST
        product_id = input_data.get('product_id', None)
        etc_title_id = input_data.get('etc_title_id', None)
        contents = input_data.get('contents', None)
        # 필수 입력 정보 확인
        if not product_id:
            return JsonResponse({'message' : '수정할 제품 id가 입력되지 않았습니다'}, status = 403)

        if not etc_title_id:
            return JsonResponse({'message' : '비고란 id가 입력되지 않았습니다.'}, status = 403)

        if not contents:
            return JsonResponse({'message' : '비고에 들어갈 내용이 입력되지 않았습니다.'}, status = 403)

        # 제품 확인
        if not Product.objects.filter(id = product_id).exists():
            return JsonResponse({'message' : '존재하지 않는 제품입니다. '}, status = 403)

        try:
            with transaction.atomic():        
                # 이미 등록된 정보가 있는지 확인
                obj , created = ProductEtcDesc.objects.update_or_create(product_id = product_id, etc_title_id = etc_title_id,
                defaults={
                    'product_id' : product_id,
                    'etc_title_id' :etc_title_id,
                    'contents' : contents
                })
                
            if created == False:
                return JsonResponse({'message' : '기존의 비고란 내용을 수정 했습니다.'}, status = 200)
            else:
                return JsonResponse({'message' : '새로운 비고란 내용을 생성 했습니다.'}, status = 200)
        except:
            return JsonResponse({'message' : '예외 사항이 발생했습니다.'}, status = 200)
    
    def get(self, request):

        filter_options = {
            'product_id' : 'product_id__exact',
        }        

        filter_set = { filter_options.get(key) : value for (key, value) in request.GET.items() if filter_options.get(key) }
        
        result = list(ProductEtcDesc.objects.filter(**filter_set).values())
        
        return JsonResponse({'message' : result}, status = 200)
###########################################################################################################
