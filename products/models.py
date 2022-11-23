from django.db      import models
from users.models   import User
from companies.models import *

class ProductGroup(models.Model):
    name        = models.CharField(max_length = 60, blank = False)
    code        = models.CharField(max_length = 10, blank = False)
    etc         = models.CharField(max_length = 3000)
    status      = models.BooleanField(default = True)

    class Meta:
        db_table = 'product_groups'

# -----------------------------------------------------------------

# Depth 1
class ProductD1(models.Model):
    productgroup_code = models.CharField(max_length = 10, blank = False)
    productgroup_num  = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    keyword       = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    created_at    = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'productD1'

# D1 - company 코드 
class ProductD1Company(models.Model):
    productD1 = models.ForeignKey('ProductD1', on_delete = models.CASCADE)
    company_code = models.CharField(max_length = 10)

# Depth 2
class ProductD2(models.Model):
    productgroup_code = models.CharField(max_length = 10, blank = False)
    productgroup_num  = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    keyword       = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    created_at    = models.DateTimeField(auto_now_add = True)

    class Meta:
        db_table = 'productD2'

class ProductD2Company(models.Model):
    productD2 = models.ForeignKey('ProductD2', on_delete = models.CASCADE)
    company_code = models.CharField(max_length = 10)

class ProductD2Composition(models.Model):
    productD2 = models.ForeignKey('ProductD2', on_delete = models.CASCADE)
    productD1 = models.ForeignKey('ProductD1', on_delete = models.CASCADE)
    quantity  = models.IntegerField()
    
    class Meta:
        db_table = 'productD2_composition'

# Depth 3
class ProductD3(models.Model):
    productgroup_code = models.CharField(max_length = 10, blank = False)
    productgroup_num  = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    keyword       = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    created_at    = models.DateTimeField(auto_now_add = True)

    class Meta:
        db_table = 'productD3'

class ProductD3Company(models.Model):
    productD3 = models.ForeignKey('ProductD3', on_delete = models.CASCADE)
    company_code = models.CharField(max_length = 10)

class ProductD3Composition1(models.Model):
    productD3 = models.ForeignKey('ProductD3', on_delete = models.CASCADE)
    productD1 = models.ForeignKey('ProductD1', on_delete = models.CASCADE)
    com_quan = models.IntegerField()

    class Meta:
        db_table = 'productD3_composition_D1'

class ProductD3Composition2(models.Model):
    productD3 = models.ForeignKey('ProductD3', on_delete = models.CASCADE)
    productD2 = models.ForeignKey('ProductD2', on_delete = models.CASCADE)
    com_quan = models.IntegerField()

    class Meta:
        db_table = 'productD3_composition_D2'


#-----------------------------------------------------
#-----------------------------------------

class ProductEtcTitle(models.Model):
    title  = models.CharField(max_length = 300, blank = False)
    status = models.BooleanField(default = False)

    class Meta:
        db_table = 'product_etc_title'

class ProductEtcDesc(models.Model):
    product_code = models.CharField(max_length = 10, blank = False)
    product_etc_title = models.ForeignKey('ProductEtcTitle', on_delete = models.CASCADE)
    contents = models.CharField(max_length = 700)

    class Meta:
        db_table = 'product_etc_desc'

############################################


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