from django.http        import JsonResponse
from products.models    import *
from datetime           import datetime
from django.db          import transaction
from django.db.models   import Q

def product_history_generator(code, quantity, price ,etc):
        now = datetime.now()
        year    = str(now.year)
        month   = str(now.month).zfill(2)
        day     = str(now.day).zfill(2)
        today = year[2:4] + month + day
        
        try:
            # 오늘 처음 물량입고 = 제품 새로 등록
            product_his = ProductHis.objects.filter(code = code)
            if not product_his.exists(): 
                for i in range(1, int(quantity) + 1):
                    product_quantity = str(i).zfill(3)
                    root_num = "01"
                    barcode  = code + today + root_num + product_quantity

                    ProductHis.objects.create(
                    use_status = 1,
                    code = code,
                    price = price,
                    barcode = barcode,
                    etc = etc)
                    
                return print('새로운 히스토리 생성')
            
            else: # 기존 등록된 제품 입고 
                # product_code 기준 가장 마지막 제품 히스토리를 가져옴 
                latest_product_his = ProductHis.objects.filter(code = code).latest('created_at')
                latest_product_barcode_yymmdd = latest_product_his.barcode[7:13] # 날짜 추출 YYMMDD

                # 가장 마지막 제품의 히스토리의 날짜와 같다 같은 제품이 다른 로트로 입고된다.
                if latest_product_barcode_yymmdd == today:
                    root_num = latest_product_his.barcode[13:15]
                    print(root_num)
                    
                    for i in range(1 , int(quantity) +1):
                        product_quantity = str(i).zfill(3)
                        root_num2 = str(int(root_num) + 1).zfill(2)
                        print(root_num2)
                        barcode = code + today + root_num2 + product_quantity
                        
                        ProductHis.objects.create(
                            use_status = 1,
                            code = code,
                            status = 1,
                            price = price,
                            barcode = barcode,
                            etc = etc
                        )
                    return print('기존 제품을 참고하여 히스토리 생성완료')
                # 새로운 날 제품이 들어오기 때문에 로트는 1로 지정
                else:
                    for i in range(1 , int(quantity) +1):
                        product_quantity = str(i).zfill(3)
                        root_num2 = "01"
                        barcode = code + today + root_num2 + product_quantity
                        
                        ProductHis.objects.create(
                            use_status = 1,
                            code = code,
                            status = 1,
                            price = price,
                            barcode = barcode,
                            etc = etc
                        )
                    return print('기존 제품을 참고하여 히스토리 생성완료 - 2')

        except KeyError:
            return JsonResponse({'message' : 'Key Error'}, status = 403)

def code_generator_d1(pg_code, cp_code):
        product_group  = ProductGroup.objects.filter(code = pg_code)
        company        = Company.objects.filter(code = cp_code)
        
        # 제품 그룹이 있는지 체크
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')
        # 회사가 등록이 되어있는지
        if company.exists() == False:
            raise ValueError('Company (trade name) that does not exist.')

        CPPG = cp_code + pg_code # SSPP 
        # 형번을 생성 등록된 제품 정보를 참고해 CPPG 가 존재하면 그 다음 형번을 부여 없으면 1로 시작.
        if ProductD1.objects.filter(code__icontains = CPPG).exists():
            latest_product_code = ProductD1.objects.filter(code__icontains = CPPG).latest('created_at').code
            model_number = int(latest_product_code[5:7]) + 1
        else:
            model_number = 1

        model_number = str(model_number).zfill(3)
        # 제품 시리얼 코드 생성 SSPP001
        product_D1_code = cp_code + pg_code + model_number
        
        return product_D1_code

def code_generator_d2(pg_code, cp_code):
        product_group  = ProductGroup.objects.filter(code = pg_code)
        company        = Company.objects.filter(code = cp_code)
        
        # 제품 그룹이 있는지 체크
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')
        # 회사가 등록이 되어있는지
        if company.exists() == False:
            raise ValueError('Company (trade name) that does not exist.')

        CPPG = cp_code + pg_code # SSPP 
        # 형번을 생성 등록된 제품 정보를 참고해 CPPG 가 존재하면 그 다음 형번을 부여 없으면 1로 시작.
        if ProductD2.objects.filter(code__icontains = CPPG).exists():
            latest_product_code = ProductD2.objects.filter(code__icontains = CPPG).latest('created_at').code
            model_number = int(latest_product_code[5:7]) + 1
        else:
            model_number = 1

        model_number = str(model_number).zfill(3)
        # 제품 시리얼 코드 생성 SSPP001
        d2_code = cp_code + pg_code + model_number
        
        return d2_code

def code_generator_d3(pg_code, cp_code):
        product_group  = ProductGroup.objects.filter(code = pg_code)
        company        = Company.objects.filter(code = cp_code)
        
        # 제품 그룹이 있는지 체크
        if product_group.exists() == False:
            raise ValueError('Product group that does not exist.')
        # 회사가 등록이 되어있는지
        if company.exists() == False:
            raise ValueError('Company (trade name) that does not exist.')

        CPPG = cp_code + pg_code # SSPP 
        # 형번을 생성 등록된 제품 정보를 참고해 CPPG 가 존재하면 그 다음 형번을 부여 없으면 1로 시작.
        if ProductD3.objects.filter(code__icontains = CPPG).exists():
            latest_product_code = ProductD3.objects.filter(code__icontains = CPPG).latest('created_at').code
            model_number = int(latest_product_code[5:7]) + 1
        else:
            model_number = 1

        model_number = str(model_number).zfill(3)
        # 제품 시리얼 코드 생성 SSPP001
        d3_code = cp_code + pg_code + model_number
        
        return d3_code



# def print_barcode(product_code, yymmdd):
#     # 제품 정보에서 name 가져옴 (product_code를 이용)
#     name = ProductInfo.objects.get(product_code = product_code).name
    
#     # product_code와 yymmdd를 바코드안에 넣어서 원하는 값을 찾음
#     barcodes = ProductHis.objects.filter(
#         Q(product_code = product_code) & Q(barcode__icontains = yymmdd)
#     ).values('barcode')
    
#     dict_print = [] # 딕셔너리를 생성한 뒤 수정사항 반영.
#     for i in range(len(barcodes)):
#         dictx = dict({'name' : name, 'barcode' : barcodes[i]['barcode']})
#         dict_print.append(dictx)

#     return dict_print


# def update_product_his(product_code):
#     count = ProductHis.objects.filter(product_code = product_code, use_status = 1).count()
#     ProductInfo.objects.filter(product_code = product_code).update(quantity = count, updated_at = datetime.now())

# def update_price(product_code, price, company_code):
#     # manage_tag 를 이용하여 입고, 출고 구분
#     # 입고
#     if Company.objects.get(code = company_code).manage_tag == "입고":
        
#         new, created = CompanyInboundPrice.objects.update_or_create(
#             company_code = company_code, product_code = product_code,
#             defaults={
#                 'resent_price' : price
#             })
        
#         return print(f'제품 코드{product_code}이 {price}원에 {company_code}에서 입고되었습니다.')
#     # 출고
#     elif Company.objects.get(code = company_code).manage_tag == "출고":
        
#         new, created = CompanyOutboundPrice.objects.update_or_create(
#             company_code = company_code, product_code = product_code,
#             defaults={
#                 'resent_price' : price
#             })
            
#         return print(f'제품 코드{product_code}이 {price}원에 {company_code}에서 출고되었습니다.')

# def set_product_history_generator(set_product_code, quantity, price, etc):
#     now     = datetime.now()
#     year    = str(now.year)
#     month   = str(now.month).zfill(2)
#     day     = str(now.day).zfill(2)
#     today = year[2:4] + month + day   

#     try:
#         with transaction.atomic():
#             # 기존 세트 상품이 있는지 확인
#             set_product_his = SetProductHis.objects.filter(set_product_code = set_product_code)
#             if not set_product_his.exists():
#                 for i in range(1, int(quantity) + 1):
#                     set_product_quantity = str(i).zfill(3)
#                     root_num = '01'
#                     barcode = set_product_code + today + root_num + set_product_quantity

#                     SetProductHis.objects.create(
#                         use_status = 1,
#                         set_product_code = set_product_code,
#                         price = price,
#                         barcode = barcode,
#                         etc = etc
#                     )
#                 return print('새로운 세트 상품 히스토리 생성완료')
#             else: #기존에 등록된 세트 상품
#                 # set_product_code 기준 가장 마지막 상품의 히스토리 가져옴
#                 latest_set_product_his = SetProductHis.objects.filter(set_product_code = set_product_code).latest('created_at')
#                 barcode_yymmdd = latest_set_product_his.barcode[7:13]

#                 if barcode_yymmdd == today:
#                     root_num = latest_set_product_his.barcode[13:15]

#                     for i in range(1, int(quantity) + 1):
#                         set_product_quantity = str(i).zfill(3)
#                         root_num2 = str(int(root_num) + 1).zfill(2)
#                         barcode = set_product_code + today + root_num2 + set_product_quantity

#                         SetProductHis.objects.create(
#                             use_status = 1,
#                             set_product_code = set_product_code,
#                             price = price,
#                             barcode = barcode,
#                             etc = etc
#                         )
#                 # 새로운 날 세트 상품이 들어오기 때문에 로트는 1로 지정
#                 else:
#                     for i in range(1, int(quantity)+1):
#                         set_product_quantity = str(i).zfill(3)
#                         root_num2 = "01"
#                         barcode = set_product_code + today + root_num2 + set_product_quantity

#                         SetProductHis.objects.create(
#                             use_status = 1,
#                             set_product_code = set_product_code,
#                             price = price,
#                             barcode = barcode,
#                             etc = etc
#                         )
#             return print('기존 제품을 참고하여 히스토리 생성완료')
#     except KeyError:
#         return JsonResponse({'message' : 'Key Error'}, status = 403)