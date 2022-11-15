from django.db       import models
from products.models import *
# Create your models here.
class Location(models.Model):
    code = 

class LocationProduct(models.Model):
    Location_code  = models.CharField(max_length=20, blank= False)
    product_code   = models.CharField(max_length = 10, blank = False)
    desc           = models.CharField(max_length=20 , blank = False)
    quantity       = models.IntegerField(default = 0)
    created_at     = models.DateTimeField(auto_now_add = True)

    class Meta:
        db_table = 'location_product'