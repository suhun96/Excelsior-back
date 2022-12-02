from django.db import models

from users.models import *
from products.models import *
from companies.models import *

class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code = models.CharField(max_length= 10)
    inbound_price = models.IntegerField(default=0)
    outbound_price = models.IntegerField(default=0)

    class Meta:
        db_table = 'inventory_price'

class Sheet(models.Model):
    user       = models.ForeignKey(User, on_delete= models.CASCADE)
    type       = models.CharField(max_length= 30)
    doc_no     = models.CharField(max_length = 60, default= 0)
    status     = models.BooleanField(default= True)
    etc        = models.CharField(max_length= 500)
    created_at = models.DateField(auto_now= True)
    updated_at = models.DateField(auto_now= True)

    class Meta:
        db_table = 'sheet'

class SheetComposition(models.Model):
    sheet      = models.ForeignKey(Sheet, on_delete = models.CASCADE)
    product    = models.ForeignKey(Product, on_delete = models.CASCADE)
    unit_price = models.IntegerField(default = 0)
    quantity   = models.IntegerField(default = 0)
    warehouse_code = models.CharField(max_length = 20)
    location   = models.CharField(max_length = 300)

    class Meta:
        db_table = 'sheet_composition'

class StockByWarehouse(models.Model):
    sheet = models.ForeignKey(Sheet, on_delete = models.CASCADE)
    warehouse_code = models.CharField(max_length=20)
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    stock_quantity = models.IntegerField(default = 0)    

    class Meta:
        db_table = 'stock_by_warehouse'

class SerialAction(models.Model):
    serial   = models.CharField(max_length=100)
    create   = models.ForeignKey(Sheet, related_name = 'create' , on_delete = models.CASCADE)
    outbound = models.ForeignKey(Sheet, related_name = 'outbound', on_delete = models.CASCADE)
    transfer = models.ForeignKey(Sheet, related_name = 'transfer', on_delete = models.CASCADE)
    compose  = models.ForeignKey(Sheet, related_name = 'compose', on_delete = models.CASCADE)

    class Meta:
        db_table = 'serial_action'

class SerialComposeRecord(models.Model):
    standard = models.ForeignKey(SerialAction, related_name = 'main', on_delete = models.CASCADE)
    compose  = models.ForeignKey(SerialAction, related_name = 'composition', on_delete = models.CASCADE)    

    class Meta:
        db_table = 'serial_compose_record'
