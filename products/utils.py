from django.http        import JsonResponse
from products.models    import *
from companies.models   import *
from django.db.models   import Sum

from stock.models       import *

import telegram
from my_settings        import TELEGRAM_TOKEN, CHAT_ID

TELEGRAM_TOKEN = TELEGRAM_TOKEN
CHAT_ID = CHAT_ID

def telegram_bot():
    bot = telegram.Bot(token = TELEGRAM_TOKEN)

    data = QuantityByWarehouse.objects.filter().values('product').annotate(total = Sum('total_quantity'))
    
    long_text = "[🤖 재고알림봇!]\n"

    for i in data:
        product_id = i['product']
        total      = i['total']
        product_get = Product.objects.get(id = product_id)
        
        safe_quantity = product_get.safe_quantity
        name          = product_get.name
        product_code  = product_get.product_code
    
        if safe_quantity > i['total']:
            text = f"제품 {name}({product_code}) 재고가 안전 재고 이하로 떨어졌습니다.  {total} / {safe_quantity} \n"
            long_text = long_text + text
    
    bot.sendMessage(chat_id = CHAT_ID, text = long_text)