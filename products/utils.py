from django.http        import JsonResponse
from products.models    import *
from companies.models   import *
from django.db.models   import Sum

from stock.models       import *

import telegram

from my_settings        import TELEGRAM_TOKEN, CHAT_ID

def telegram_bot(new_sheet_id):
    bot = telegram.Bot(token = TELEGRAM_TOKEN)
    
    long_text = "[🤖 재고알림봇!]\n"
    count = 0
    products = SheetComposition.objects.filter(sheet_id = new_sheet_id).values('product')


    for product in products:
        product_id = product['product']
        product      = Product.objects.get(id = product_id)
        product_code = product.product_code
        
        TOTAL        = QuantityByWarehouse.objects.filter(product_id = product_id).values('product').annotate(quantity = Sum('total_quantity'))
    

        safe_quantity = product.safe_quantity
        name          = product.name
        product_code  = product.product_code
    
        if safe_quantity > TOTAL[0]['quantity']:
            count += 1
            text = f"제품 {name}({product_code}) 재고가 안전 재고 이하로 떨어졌습니다.  {TOTAL[0]['quantity']} / {safe_quantity} \n"
            long_text = long_text + text
    
    if count > 0:
        bot.sendMessage(chat_id = CHAT_ID, text = long_text)