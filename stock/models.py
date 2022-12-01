from django.db import models

from users.models import *
from products.models import *
from companies.models import *

class TotalProductQuantity(models.Model):
    product = models.ForeignKey(Product , on_delete= models.CASCADE)
    total_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'inventory_quantity'

class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code = models.CharField(max_length= 10)
    inbound_price = models.IntegerField(default=0)
    outbound_price = models.IntegerField(default=0)

    class Meta:
        db_table = 'inventory_price'

# class ChangeQuantity(models.Model):
#     product         = models.ForeignKey(Product, on_delete= models.CASCADE)
#     quantity        = models.IntegerField()
#     created_at      = models.DateField(auto_now = True)

class InventorySheet(models.Model):
    user            = models.ForeignKey(User, on_delete= models.CASCADE)
    is_inbound      = models.CharField(max_length= 30)
    product         = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code    = models.CharField(max_length= 20, blank= False)
    warehouse_code  = models.CharField(max_length= 10)
    unit_price      = models.IntegerField(default= 0)
    before_quantity = models.IntegerField(default= 0)
    after_quantity  = models.IntegerField(default= 0)
    quantity        = models.IntegerField(default= 0)
    etc             = models.CharField(max_length= 500)
    status          = models.BooleanField(default= True)
    created_at      = models.DateField(auto_now= True)
    updated_at      = models.DateField(auto_now= True)

    class Meta:
        db_table = 'inventory_sheet'

class InventorySheetLog(models.Model):
    user            = models.ForeignKey(User, on_delete= models.CASCADE)
    process_type    = models.CharField(max_length= 100)
    inventorysheet  = models.ForeignKey(InventorySheet, on_delete= models.CASCADE)
    is_inbound      = models.CharField(max_length= 30)
    product         = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code    = models.CharField(max_length= 20, blank= False)
    warehouse_code  = models.CharField(max_length= 10)
    unit_price      = models.IntegerField(default= 0)
    before_quantity = models.IntegerField(default= 0)
    after_quantity  = models.IntegerField(default= 0)
    quantity        = models.IntegerField(default= 0)
    etc             = models.CharField(max_length= 500)
    status          = models.BooleanField(default= False)
    created_at      = models.DateField(auto_now= True)
    updated_at      = models.DateField(auto_now= True)

    class Meta:
<<<<<<< HEAD
        db_table = 'product_inbound'

class ProductOutbound(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    company_code   = models.CharField(max_length = 20, blank= False)
    warehouse_code = models.CharField(max_length = 20)
    unit_price = models.IntegerField(default= 0)
    quantity = models.IntegerField(default= 0)
    etc = models.CharField(max_length= 300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_outbound'

class SetProduction(models.Model):
    set_product = models.ForeignKey(Product, on_delete= models.CASCADE)
    quantity = models.IntegerField(default= 0)
    etc = models.CharField(max_length= 300)
    created_at = models.DateTimeField(auto_now_add= True)

    class Meta:
        db_table = 'set_productions'
=======
        db_table = 'inventory_sheet_log'    
>>>>>>> 81329038cea85ca24a1715ade0f4246fd9ad7a1e
