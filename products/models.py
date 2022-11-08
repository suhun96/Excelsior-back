from django.db      import models
from users.models   import User

class ProductGroup(models.Model):
    name        = models.CharField(max_length = 60, blank = False)
    code        = models.CharField(max_length = 10, blank = False)
    etc         = models.CharField(max_length = 3000)

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

    class Meta:
        db_table = 'companies'

# -----------------------------------------------------------------

# Depth 1
class Component(models.Model):
    code          = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    etc           = models.CharField(max_length = 3000, blank = True)

    class Meta:
        db_table = 'components'

# Depth 2
class Bom(models.Model):
    code          = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    etc           = models.CharField(max_length = 3000, blank = True)

    class Meta:
        db_table = 'boms'

class BomComponent(models.Model):
    bom_code = models.CharField(max_length = 10, blank = False)
    com_code = models.CharField(max_length = 10, blank = False)
    com_quan = models.IntegerField()
    
    class Meta:
        db_table = 'bom_components'

# Depth 3
class Set(models.Model):
    code          = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)
    etc          = models.CharField(max_length = 3000, blank = True)

    class Meta:
        db_table = 'sets'

class SetComponent(models.Model):
    set_code = models.CharField(max_length = 10, blank = False)
    com_code = models.CharField(max_length = 10, blank = False)
    com_quan = models.IntegerField()

    class Meta:
        db_table = 'set_components'

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