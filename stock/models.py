from datetime   import datetime
from django.db  import models

from users.models import *
from products.models import *
from companies.models import *


class Sheet(models.Model):
    user       = models.ForeignKey(User, on_delete= models.CASCADE)
    type       = models.CharField(max_length= 30)
    company    = models.ForeignKey(Company, on_delete= models.CASCADE, null= True)
    status     = models.BooleanField(default= True)
    etc        = models.CharField(max_length= 500)
    date       = models.DateField(default= datetime.now())
    document_num = models.CharField(max_length= 100, default= 'fix')
    related_sheet_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now= True)

    class Meta:
        db_table = 'sheet'

class SheetComposition(models.Model):
    sheet      = models.ForeignKey(Sheet, on_delete = models.CASCADE)
    product    = models.ForeignKey(Product, on_delete = models.CASCADE)
    unit_price = models.IntegerField(default = 0)
    quantity   = models.IntegerField(default = 0)
    warehouse_code = models.CharField(max_length = 20)
    location   = models.CharField(max_length = 300) 
    etc        = models.CharField(max_length = 300)

    class Meta:
        db_table = 'sheet_detail'

class SheetLog(models.Model):
    sheet_id   = models.IntegerField()
    user_name  = models.CharField(max_length=50)
    type       = models.CharField(max_length= 30)
    company    = models.ForeignKey(Company, on_delete= models.CASCADE)
    status     = models.BooleanField(default= True)
    etc        = models.CharField(max_length= 500)
    created_at = models.DateTimeField(auto_now_add= True)

    class Meta:
        db_table = 'sheet_logs'

class SheetCompositionLog(models.Model):
    sheet_log   = models.ForeignKey(SheetLog, on_delete= models.CASCADE, related_name= 'sheet_log')
    product     = models.ForeignKey(Product, on_delete = models.CASCADE)
    unit_price  = models.IntegerField(default = 0)
    quantity    = models.IntegerField(default = 0)
    warehouse_code = models.CharField(max_length = 20)
    location    = models.CharField(max_length = 300) 
    etc         = models.CharField(max_length = 300)

    class Meta:
        db_table = 'sheet_log_composition'

class StockByWarehouse(models.Model):
    sheet = models.ForeignKey(Sheet, on_delete = models.CASCADE)
    warehouse_code = models.CharField(max_length=20)
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    stock_quantity = models.IntegerField(default = 0)    

    class Meta:
        db_table = 'stock_by_warehouse'

class QuantityByWarehouse(models.Model):
    warehouse_code = models.CharField(max_length=20)
    product        = models.ForeignKey(Product, on_delete= models.CASCADE)
    total_quantity = models.IntegerField(default = 0)

    class Meta:
        db_table = 'quantity_by_warehouse'

class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    company = models.ForeignKey(Company, on_delete= models.CASCADE)
    inbound_price = models.IntegerField(default=0)
    outbound_price = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_price'

##############################################################################################################

class SerialCode(models.Model):
    sheet_id   = models.IntegerField()
    product_id = models.IntegerField()
    code       = models.CharField(max_length= 100)
    status     = models.BooleanField(default= True)
    
    class Meta:
        db_table = 'serial_codes'

class SerialCodeTitle(models.Model):
    title  = models.CharField(max_length= 100)
    status = models.BooleanField(default= True)

    class Meta:
        db_table = 'serial_code_titles'

class SerialCodeValue(models.Model):
    title       = models.ForeignKey(SerialCodeTitle, on_delete= models.CASCADE)
    serial_code = models.ForeignKey(SerialCode, on_delete= models.CASCADE, related_name= 'serial_code_value')
    contents    = models.CharField(max_length= 255)
    user        = models.ForeignKey(User, on_delete= models.CASCADE, default=1)
    date        = models.DateTimeField(auto_now= True)

    class Meta:
        db_table = 'serial_code_value'

############################################################################################################

class MovingAverageMethod(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE)
    average_price  = models.IntegerField()
    custom_price   = models.IntegerField(null= True)
    total_quantity = models.IntegerField()

    class Meta:
        db_table = 'moving_average_method'

