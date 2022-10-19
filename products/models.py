from django.db      import models
from users.models   import User

class ProductGroup(models.Model):
    name        = models.CharField(max_length = 60, blank = False)
    code        = models.CharField(max_length = 10, blank = False)
    etc         = models.CharField(max_length = 3000)
    created_at  = models.DateTimeField(auto_now_add = True)
    updated_at  = models.DateTimeField(auto_now = True)

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
    created_at  = models.DateTimeField(auto_now_add = True)
    updated_at  = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'companies'

class UseStatus(models.Model):
    name = models.CharField(max_length = 15, blank = False)

    class Meta:
        db_table = 'use_status'

class Product(models.Model):
    product_group   = models.ForeignKey(ProductGroup, on_delete = models.CASCADE)
    company         = models.ForeignKey(Company, on_delete = models.CASCADE)
    use_status      = models.ForeignKey(UseStatus, on_delete = models.CASCADE)
    serial_code     = models.CharField(max_length = 25, blank = False)
    name            = models.CharField(max_length = 15, blank = False)
    serch_word      = models.CharField(max_length = 150, blank = False)
    price           = models.BigIntegerField()
    quantity        = models.IntegerField()
    safe_quantity   = models.IntegerField()
    etc             = models.CharField(max_length = 3000, blank = False)
    created_at      = models.DateTimeField(auto_now_add = True)
    updated_at      = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'products'

class WarehousingOrder(models.Model):
    user    = models.ForeignKey(User, on_delete = models.CASCADE)
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    company = models.ForeignKey(Company, on_delete = models.CASCADE)
    inbound_price   = models.BigIntegerField()
    inbound_quntity = models.IntegerField()
    inbound_address = models.CharField(max_length = 200, blank = False)
    created_at      = models.DateTimeField(auto_now_add = True)
    updated_at      = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'warehousing_orders'