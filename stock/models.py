from django.db import models

from users.models import *
from products.models import *
from companies.models import *

class ProductQuantity(models.Model):
    product = models.ForeignKey(Product , on_delete= models.CASCADE)
    total_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_quantity'

class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code = models.CharField(max_length= 10)
    inbound_price = models.IntegerField(default=0)
    outbound_price = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_price'

class ProductWarehouse(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    warehouse_code = models.CharField(max_length= 10)
    stock_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_warehouse'

class ProductInbound(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code   = models.CharField(max_length = 20, blank= False)
    warehouse_code = models.CharField(max_length = 20)
    unit_price = models.IntegerField(default=0)
    quantity = models.IntegerField(default= 0)
    etc = models.CharField(max_length= 300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_inbound'