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
    product_code  = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)

    class Meta:
        db_table = 'components'

# Depth 2
class Bom(models.Model):
    product_code  = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)

    class Meta:
        db_table = 'boms'

# Depth 3
class Set(models.Model):
    product_code  = models.CharField(max_length = 10, blank = False)
    quantity      = models.IntegerField()
    safe_quantity = models.IntegerField()
    search_word   = models.CharField(max_length = 150, blank = False)
    name          = models.CharField(max_length = 100, blank = False)

    class Meta:
        db_table = 'sets'

# -------------------------------------------------------------------

class ProductHis(models.Model):
    product_code = models.CharField(max_length = 10, blank = False)
    status       = models.IntegerField(blank = False)
    price        = models.BigIntegerField()
    barcode      = models.CharField(max_length = 20, blank = False)
    etc          = models.CharField(max_length = 3000, blank = True)
    created_at   = models.DateTimeField(auto_now_add = True)
    updated_at   = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'product_his'

class BomComponent(models.Model):
    bom_code = models.CharField(max_length = 10, blank = False)
    com_code = models.CharField(max_length = 10, blank = False)
    com_quan = models.IntegerField()
    
    class Meta:
        db_table = 'bom_components'

class SetComponent(models.Model):
    set_code = models.CharField(max_length = 10, blank = False)
    com_code = models.CharField(max_length = 10, blank = False)
    com_quan = models.IntegerField()

    class Meta:
        db_table = 'set_components'
