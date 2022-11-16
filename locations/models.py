from django.db       import models
from products.models import *
# Create your models here.

class Warehouse(models.Model):
    name   = models.CharField(max_length = 60, blank = False)
    code   = models.CharField(max_length = 20, blank = False)
    type   = models.CharField(max_length = 40, blank = True)
    way    = models.CharField(max_length = 100, blank = True )
    etc    = models.CharField(max_length = 1000, blank = True )
    status = models.BooleanField(default= True)
    
    class Meta:
        db_table = 'warehouse'

class WarehouseProperty(models.Model):
    contents = models.CharField(max_length = 100, blank = False)
    status = models.BooleanField(default= True)

    class Meta:
        db_table = 'warehouse_property'

class WarehouseType(models.Model):
    contents = models.CharField(max_length = 100, blank = False)
    status = models.BooleanField(default= True)

    class Meta:
        db_table = 'warehouse_type'   

class LocationProduct(models.Model):
    warehouse_code = models.CharField(max_length = 20, blank= False)
    location_desc  = models.CharField(max_length = 80, blank = False)
    product_code   = models.CharField(max_length = 10, blank = False)
    quantity       = models.IntegerField(default = 0)
    created_at     = models.DateTimeField(auto_now_add = True)

    class Meta:
        db_table = 'location_product'