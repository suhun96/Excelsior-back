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

class ProductEtcTitle(models.Model):
    title  = models.CharField(max_length=100, blank = False)
    status = models.BooleanField(default = False)

    class Meta:
        db_table = 'product_etc_title'

class ProductD1EtcDesc(models.Model):
    productD1 = models.ForeignKey('ProductD1', on_delete= models.CASCADE)
    product_etc_title = models.ForeignKey('ProductEtcTitle', on_delete= models.CASCADE)
    contents = models.CharField(max_length = 700) 
    
    class Meta:
        db_table = 'productD1_etc_desc'

class ProductD2EtcDesc(models.Model):
    productD2 = models.ForeignKey('ProductD2', on_delete= models.CASCADE)
    product_etc_title = models.ForeignKey('ProductEtcTitle', on_delete= models.CASCADE)
    contents = models.CharField(max_length = 700) 
    
    class Meta:
        db_table = 'productD2_etc_desc'

class ProductD3EtcDesc(models.Model):
    productD3 = models.ForeignKey('ProductD3', on_delete= models.CASCADE)
    product_etc_title = models.ForeignKey('ProductEtcTitle', on_delete= models.CASCADE)
    contents = models.CharField(max_length = 700) 
    
    class Meta:
        db_table = 'productD3_etc_desc'

# -------------------------------------------------------------------------- #

# Depth 1
class ProductD1(models.Model):
    company_code      = models.CharField(max_length = 10) 
    productgroup_code = models.CharField(max_length = 10, blank = False)
    product_num       = models.CharField(max_length = 10, blank = False)
    quantity          = models.IntegerField(default = 0)
    safe_quantity     = models.IntegerField(default = 0)
    keyword           = models.CharField(max_length = 150)
    name              = models.CharField(max_length = 100, blank = False)
    warehouse_code    = models.CharField(max_length = 10)
    location          = models.CharField(max_length = 100)
    status            = models.BooleanField(default= True)
    created_at        = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'productD1'


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

    class Meta:
        db_table = 'productD2_company'

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

    class Meta:
        db_table = 'productD3_company'

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

