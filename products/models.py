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
        db_table = 'product_custom_title'

class ProductEtcDesc(models.Model):
    product   = models.ForeignKey('Product', on_delete= models.CASCADE)
    etc_title = models.ForeignKey('ProductEtcTitle', on_delete= models.CASCADE)
    contents  = models.CharField(max_length = 700) 
    
    class Meta:
        db_table = 'product_custom_desc'
# -------------------------------------------------------------------------- #

# Depth 1
class Product(models.Model):
    is_set            = models.BooleanField(default=False)
    is_serial         = models.BooleanField(default=False)
    labor             = models.IntegerField(default=0, null=True)
    company           = models.ForeignKey(Company, on_delete= models.CASCADE, null= True) 
    product_group     = models.ForeignKey(ProductGroup, on_delete= models.CASCADE)
    product_num       = models.CharField(max_length = 10, blank = False)
    product_code      = models.CharField(max_length = 10, blank = False)
    safe_quantity     = models.IntegerField(default = 0)
    keyword           = models.CharField(max_length = 150)
    name              = models.CharField(max_length = 100, blank = False)
    warehouse_code    = models.CharField(max_length = 10)
    location          = models.CharField(max_length = 100)
    status            = models.BooleanField(default= True)
    barcode           = models.CharField(max_length= 30, default=0)
    created_at        = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        db_table = 'product'

class ProductComposition(models.Model):
    set_product         = models.ForeignKey('Product', on_delete = models.CASCADE)
    composition_product = models.ForeignKey('Product', on_delete = models.CASCADE, related_name = 'composition_product')
    quantity            = models.IntegerField()
    
    class Meta:
        db_table = 'product_composition'

