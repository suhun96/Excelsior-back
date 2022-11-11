from django.db      import models
from users.models   import User

class ProductGroup(models.Model):
    name        = models.CharField(max_length = 60, blank = False)
    code        = models.CharField(max_length = 10, blank = False)
    etc         = models.CharField(max_length = 3000)

    class Meta:
        db_table = 'product_groups'

class Company(models.Model): # managers 확인 하세요!
    name         = models.CharField(max_length = 60, blank = False)
    keyword      = models.CharField(max_length = 150)
    code         = models.CharField(max_length = 10, blank = False)
    owner        = models.CharField(max_length = 30)
    biz_no       = models.CharField(max_length = 30)
    biz_type     = models.CharField(max_length = 100)
    biz_item     = models.CharField(max_length = 100)
    phone        = models.CharField(max_length = 100, blank = False)
    fax          = models.CharField(max_length = 100)
    email        = models.CharField(max_length = 100)
    address_main = models.CharField(max_length = 120)
    address_desc = models.CharField(max_length = 120)
    zip_code     = models.CharField(max_length = 100)

    class Meta:
        db_table = 'companies'

class CompanyETC(models.Model):
    comp_code = models.CharField(max_length = 10, blank = False)
    no        = models.IntegerField()
    title     = models.CharField(max_length = 120)
    contents  = models.CharField(max_length = 700) 
    status    = models.BooleanField(default = False)

    class Meta:
        db_table = 'company_etc'

class CompanyPhonebook(models.Model):
    comp_code = models.CharField(max_length = 10, blank = False)
    name    = models.CharField(max_length = 20, blank = True)
    mobile  = models.CharField(max_length = 20, blank = True)
    email   = models.CharField(max_length = 100, blank= True)
    class Meta:
        db_table = 'company_phonebook'
# -----------------------------------------------------------------

# Depth 1
class ProductD1(models.Model):
    code          = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    created_at    = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'productD1'

# Depth 2
class ProductD2(models.Model):
    code          = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)

    class Meta:
        db_table = 'productD2'

class ProductD2Composition(models.Model):
    d2_code = models.CharField(max_length = 10, blank = False)
    com_code = models.CharField(max_length = 10, blank = False)
    com_quan = models.IntegerField()
    
    class Meta:
        db_table = 'productD2_composition'

# Depth 3
class ProductD3(models.Model):
    code          = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)

    class Meta:
        db_table = 'productD3'

class ProductD3Composition(models.Model):
    d3_code = models.CharField(max_length = 10, blank = False)
    com_code = models.CharField(max_length = 10, blank = False)
    com_quan = models.IntegerField()

    class Meta:
        db_table = 'productD3_composition'

class ProductEtc(models.Model):
    product_code = models.CharField(max_length = 10, blank = False)
    no           = models.IntegerField()
    title        = models.CharField(max_length = 120, blank = False)
    contents     = models.CharField(max_length = 3000)

    class Meta:
        db_table = 'product_etc'


# barcode history
class ProductHis(models.Model):
    code         = models.CharField(max_length = 10, blank = False)
    barcode      = models.CharField(max_length = 20, blank = False)
    status       = models.IntegerField(blank = False)
    price        = models.BigIntegerField()
    created_at   = models.DateTimeField(auto_now_add = True)
    updated_at   = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'product_his'

# 입고 (Inbound)
class InboundOrder(models.Model):
    user            = models.ForeignKey(User, on_delete = models.CASCADE)
    company_code    = models.CharField(max_length = 5, blank = False)
    etc             = models.CharField(max_length = 3000, blank = True)
    created_at      = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'inbound_order'

class InboundQuantity(models.Model):
    inbound_order    = models.ForeignKey(InboundOrder, on_delete = models.CASCADE)
    product_code     = models.CharField(max_length = 10, blank = False)
    inbound_price    = models.BigIntegerField()
    inbound_quantity = models.IntegerField()
    created_at       = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'inbound_quantity'

# 출고(Outbound)
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