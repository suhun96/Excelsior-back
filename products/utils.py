from django.http        import JsonResponse
from products.models    import *
from datetime           import datetime, date

def product_history_generator(product_code, quantity, price ,etc):
        now = datetime.now()
        year    = str(now.year)
        month   = str(now.month)
        day     = str(now.day) 
        today = year[2:4] + month + day
        try:
            product_his = ProductHis.objects.filter(product_code = product_code, barcode__icontains = today)
            what = product_his.latest('created_at')
            print(what)
            print(what.barcode)
            if product_his.exists():
                slicing_num = what.barcode[7:10]
                
                for i in range(1 , int(quantity) +1):
                    zero_num = str(i + int(slicing_num)).zfill(3)
                    barcode = product_code + zero_num + today
                    
                    ProductHis.objects.create(
                        use_status = 1,
                        product_code = product_code,
                        price = price,
                        barcode = barcode,
                        etc = etc
                    )

                return print('기존 제품을 참고하여 히스토리 생성완료')
            else:
                for i in range(1, int(quantity) + 1):
                    zero_num = str(i).zfill(3)
                    barcode = product_code + zero_num + year[2:4] + month + day

                    ProductHis.objects.create(
                    use_status = 1,
                    product_code = product_code,
                    price = price,
                    barcode = barcode,
                    etc = etc)

                return print('새로운 제품 히스토리 생성완료')
        except KeyError:
            return JsonResponse({'message' : '키 에러'}, status = 403)

def update_product_his(product_code, price):
    count = ProductHis.objects.filter(product_code = product_code, use_status = 1).count()
    ProductInfo.objects.filter(product_code = product_code).update(quantity = count, resent_IB_price = price ,updated_at = datetime.now())