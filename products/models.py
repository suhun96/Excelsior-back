from django.db      import models
from users.models   import User

class ProductGroup(models.Model):
    name        = models.CharField(max_length = 60, blank = False)
    code        = models.CharField(max_length = 10, blank = False)
    etc         = models.CharField(max_length = 3000)
    created_at  = models.DateTimeField(auto_now_add = True)
    updated_at  = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'product_groups'

class Company(models.Model): # managers 확인 하세요!
    name        = models.CharField(max_length = 60, blank = False)
    code        = models.CharField(max_length = 10, blank = False)
    address     = models.CharField(max_length = 120, blank = False)
    managers    = models.CharField(max_length = 30, blank = False)
    telephone   = models.CharField(max_length = 20, blank = False)
    mobilephone = models.CharField(max_length = 13, blank = False)
    manage_tag  = models.CharField(max_length = 30, blank = False)
    etc         = models.CharField(max_length = 3000, blank = False)
    created_at  = models.DateTimeField(auto_now_add = True)
    updated_at  = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'companies'

class ProductHis(models.Model):
    use_status      = models.IntegerField(blank = False)
    serial_code     = models.CharField(max_length = 10, blank = False)
    price           = models.BigIntegerField()
    barcode         = models.CharField(max_length = 20, blank = False)              
    etc             = models.CharField(max_length = 3000, blank = True)
    created_at      = models.DateTimeField(auto_now_add = True)
    updated_at      = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'product_his'

class ProductInfo(models.Model):
    serial_code     = models.CharField(max_length = 10, blank = False)
    quantity        = models.IntegerField()
    safe_quantity   = models.IntegerField()
    search_word     = models.CharField(max_length = 150, blank = False)
    name            = models.CharField(max_length = 15, blank = False)
    created_at      = models.DateTimeField(auto_now_add = True)
    updated_at      = models.DateTimeField(auto_now = True)
    
    class Meta:
        db_table = 'product_info'

class InboundOrder(models.Model):
    user            = models.ForeignKey(User, on_delete = models.CASCADE)
    company_code    = models.CharField(max_length = 5, blank = False)
    etc             = models.CharField(max_length = 3000, blank = True)
    created_at      = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'inbound_order'

class InboundQuantity(models.Model):
    inbound_order   = models.ForeignKey(InboundOrder, on_delete = models.CASCADE)
    serial_code     = models.CharField(max_length = 10, blank = False)
    inbound_price   = models.BigIntegerField()
    inbound_quntity = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'inbound_quantity'