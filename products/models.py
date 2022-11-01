from codecs import BOM
from email.policy import default
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
    product_code    = models.CharField(max_length = 10, blank = False)
    price           = models.BigIntegerField()
    barcode         = models.CharField(max_length = 20, blank = False)              
    etc             = models.CharField(max_length = 3000, blank = True)
    created_at      = models.DateTimeField(auto_now_add = True)
    updated_at      = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'product_his'

class ProductInfo(models.Model):
    product_code    = models.CharField(max_length = 10, blank = False)
    quantity        = models.IntegerField()
    safe_quantity   = models.IntegerField()
    search_word     = models.CharField(max_length = 150, blank = False)
    name            = models.CharField(max_length = 100, blank = False)
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
    product_code    = models.CharField(max_length = 10, blank = False)
    inbound_price   = models.BigIntegerField()
    inbound_quntity = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'inbound_quantity'

class OutboundOrder(models.Model):
    user            = models.ForeignKey(User, on_delete = models.CASCADE)
    company_code    = models.CharField(max_length = 5, blank = False)
    etc             = models.CharField(max_length = 3000, blank = True)
    created_at      = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'outbound_order'

class OutboundQuantity(models.Model):
    outbound_order  = models.ForeignKey(OutboundOrder, on_delete = models.CASCADE)
    product_code    = models.CharField(max_length = 40, blank = False)
    outbound_price  = models.BigIntegerField()
    outbound_quantity = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'outbound_quantity'
        
class OutboundBarcode(models.Model):
    outbound_order = models.ForeignKey(OutboundOrder, on_delete = models.CASCADE)
    barcode    = models.CharField(max_length = 40, blank = False)
    created_at = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'outbound_barcode'

class CompanyInboundPrice(models.Model):
    product_code = models.CharField(max_length = 10, blank = False)
    company_code = models.CharField(max_length = 5, blank = False)
    resent_price = models.BigIntegerField()

    class Meta:
        db_table = 'company_inbound_price'

class CompanyOutboundPrice(models.Model):
    product_code = models.CharField(max_length = 10, blank = False)
    company_code = models.CharField(max_length = 5, blank = False)
    resent_price = models.BigIntegerField()

    class Meta:
        db_table = 'company_outbound_price'

#--------------------------------------------#

class Bom(models.Model):
    name = models.CharField(max_length = 300, blank = False)
    etc  = models.CharField(max_length = 3000, blank = True)

    class Meta:
        db_table = 'bom' 

class BomProduct(models.Model):
    BOM = models.ForeignKey(Bom, on_delete = models.CASCADE)
    product_code = models.CharField(max_length = 10, blank = False)
    product_quantity = models.IntegerField()
    product_price = models.IntegerField()

    class Meta:
        db_table = 'bom_product'

class OutboundBom(models.Model):
    outbound_order = models.ForeignKey(OutboundOrder, on_delete = models.CASCADE)
    BOM = models.ForeignKey(Bom, on_delete = models.CASCADE)

    class Meta:
        db_table = 'outbound_bom'

#------------------------------------------------#

class SetInfo(models.Model):
    set_code        = models.CharField(max_length = 10, blank = False)
    quantity        = models.IntegerField()
    safe_quantity   = models.IntegerField()
    search_word     = models.CharField(max_length = 150, blank = False)
    name            = models.CharField(max_length = 100, blank = False)
    created_at      = models.DateTimeField(auto_now_add = True)
    updated_at      = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'set_info' 

class SetProduct(models.Model):
    set_code         = models.CharField(max_length = 10, blank = False)
    product_code     = models.CharField(max_length = 10, blank = False)
    product_quantity = models.IntegerField()

    class Meta:
        db_table = 'set_info_product'

class OutboundSetQuantity(models.Model):
    outbound_order  = models.ForeignKey(OutboundOrder, on_delete = models.CASCADE)
    set_code        = models.CharField(max_length = 10, blank = False)
    quantity        = models.IntegerField()

    class Meta:
        db_table = 'outbound_set_info'
