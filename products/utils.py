from tabnanny import check
from django.http        import JsonResponse
from products.models    import *
from datetime           import datetime

def product_history_generator(product_code, quantity, price ,etc):
        now = datetime.now()
        year    = str(now.year)
        month   = str(now.month)
        day     = str(now.day) 
        today = year[2:4] + month + day
        
        try:
            # 오늘 처음 물량입고 = 제품 새로 등록
            product_his = ProductHis.objects.filter(product_code = product_code)
            
            if not product_his.exists(): 
                for i in range(1, int(quantity) + 1):
                    product_quantity = str(i).zfill(3)
                    root_num = "01"
                    barcode  = product_code + today + root_num + product_quantity

                    ProductHis.objects.create(
                    use_status = 1,
                    product_code = product_code,
                    price = price,
                    barcode = barcode,
                    etc = etc)

                return print('새로운 제품 히스토리 생성완료')
            
            else: # 기존 등록된 제품 입고 
                # product_code 기준 가장 마지막 제품 히스토리를 가져옴 
                latest_product_his = ProductHis.objects.filter(product_code = product_code).latest('created_at')
                latest_product_barcode_yymmdd = latest_product_his.barcode[7:13] # 날짜 추출 YYMMDD

                # 가장 마지막 제품의 히스토리의 날짜와 같다 같은 제품이 다른 로트로 입고된다.
                if latest_product_barcode_yymmdd == today:
                    root_num = latest_product_his.barcode[13:15]
                    
                    for i in range(1 , int(quantity) +1):
                        product_quantity = str(i).zfill(3)
                        root_num2 = str(int(root_num) + 1).zfill(2)
                        barcode = product_code + today + root_num2 + product_quantity
                        
                        ProductHis.objects.create(
                            use_status = 1,
                            product_code = product_code,
                            price = price,
                            barcode = barcode,
                            etc = etc
                        )
                # 새로운 날 제품이 들어오기 때문에 로트는 1로 지정
                else:
                    for i in range(1 , int(quantity) +1):
                        product_quantity = str(i).zfill(3)
                        root_num2 = "01"
                        barcode = product_code + today + root_num2 + product_quantity
                        
                        ProductHis.objects.create(
                            use_status = 1,
                            product_code = product_code,
                            price = price,
                            barcode = barcode,
                            etc = etc
                        )
                    

                return print('기존 제품을 참고하여 히스토리 생성완료')
        except KeyError:
            return JsonResponse({'message' : 'Key Error'}, status = 403)

def update_product_his(product_code):
    count = ProductHis.objects.filter(product_code = product_code, use_status = 1).count()
    ProductInfo.objects.filter(product_code = product_code).update(quantity = count, updated_at = datetime.now())

def update_price(product_code, price, company_code):
    if Company.objects.get(code = company_code).manage_tag == "입고":
        
        new, created = CompanyInboundPrice.objects.update_or_create(
            company_code = company_code, product_code = product_code,
            defaults={
                'resent_price' : price
            })
        
        return print(f'제품 코드{product_code}이 {price}원에 {company_code}에서 입고되었습니다.')
    
    elif Company.objects.get(code = company_code).manage_tag == "출고":
        new, created = CompanyOutboundPrice.objects.update_or_create(
            company_code = company_code, product_code = product_code,
            defaults={
                'resent_price' : price
            })
        return print(f'제품 코드{product_code}이 {price}원에 {company_code}에서 출고되었습니다.')

