from django.db import models

from users.models import *
from companies.models import *

class ProductQuantity(models.Model):
    product = models.ForeignKey('Product', on_delete= models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_quantity'

class ProductPrice(models.Model):
    product = models.ForeignKey('Product', on_delete= models.CASCADE)
    inbound_price = models.IntegerField(default=0)
    outbound_price = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_price'

class ProductInbound(models.Model):
    company = models.ForeignKey('Company', on_delete= models.CASCADE)
    product = models.ForeignKey('Product', on_delete= models.CASCADE)
    unit_price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_inbound'