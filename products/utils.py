from django.http        import JsonResponse
from products.models    import *
from companies.models   import *
from django.db.models   import Sum

from stock.models       import *

import telegram

from my_settings        import TELEGRAM_TOKEN, CHAT_ID

async def telegram_bot(new_sheet_id):
    bot = telegram.Bot(token = TELEGRAM_TOKEN)
    
    long_text = "[🤖 안전재고미만 알림]\n"
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
        product_group_name = ProductGroup.objects.get(id = product.product_group_id).name

        if safe_quantity > TOTAL[0]['quantity']:
            count += 1
            text = f"[{product_group_name}] {name}({product_code}) {TOTAL[0]['quantity']} / {safe_quantity} \n"
            long_text = long_text + text
    
    if count > 0:
        await bot.sendMessage(chat_id = CHAT_ID, text = long_text)
        Message = 'ok'
        return Message
        
        