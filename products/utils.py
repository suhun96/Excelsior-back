from django.http        import JsonResponse
from products.models    import *
from datetime           import datetime

def product_history_generator(product_serial_code, quantity, price ,etc):
        now = datetime.now()
        year    = str(now.year)
        month   = str(now.month)
        day     = str(now.day) 
        
        try:
            product_his = ProductHis.objects.filter(serial_code = product_serial_code, use_status = 1)
    
            if product_his.exists():
                before_quantity = product_his.count()
                
                for i in range(1 , int(quantity) +1):
                    zero_num = str(i + before_quantity).zfill(3)
                    barcode = product_serial_code + zero_num + year[2:4] + month + day
                    
                    ProductHis.objects.create(
                        use_status = 1,
                        serial_code = product_serial_code,
                        price = price,
                        barcode = barcode,
                        etc = etc
                    )

                return print('기존 제품을 참고하여 히스토리 생성완료')
            else:
                for i in range(1, int(quantity) + 1):
                    zero_num = str(i).zfill(3)
                    barcode = product_serial_code + zero_num + year[2:4] + month + day

                    ProductHis.objects.create(
                    use_status = 1,
                    serial_code = product_serial_code,
                    price = price,
                    barcode = barcode,
                    etc = etc)

                return print('새로운 제품 히스토리 생성완료')
        except KeyError:
            return JsonResponse({'message' : '키 에러'}, status = 403)

def update_product_his(product_serial_code, price):
    count = ProductHis.objects.filter(serial_code = product_serial_code).count()
    ProductInfo.objects.filter(serial_code = product_serial_code).update(quantity = count, resent_IB_price = price ,updated_at = datetime.now())