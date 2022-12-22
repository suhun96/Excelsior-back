from django.db import models
from products.models import *

class Company(models.Model): # managers 확인 하세요!
    name         = models.CharField(max_length = 60, blank = False)
    keyword      = models.CharField(max_length = 150)
    code         = models.CharField(max_length = 10)
    represent    = models.CharField(max_length = 30)
    biz_no       = models.CharField(max_length = 30)
    biz_type     = models.CharField(max_length = 100)
    biz_item     = models.CharField(max_length = 100)
    phone        = models.CharField(max_length = 100, blank = False)
    fax          = models.CharField(max_length = 100)
    email        = models.CharField(max_length = 100)
    address_main = models.CharField(max_length = 120)
    address_desc = models.CharField(max_length = 120)
    zip_code     = models.CharField(max_length = 100)
    status       = models.BooleanField(default = True)
    created_at   = models.DateTimeField(auto_now_add = True)
    updated_at   = models.DateField(auto_now = True)

    class Meta:
        db_table = 'companies'

# class CustomTitle(models.Model):
#     title  = models.CharField(max_length= 300, blank= False)
#     status = models.BooleanField(default= True)

#     class Meta:
#         db_table = 'company_custom_title' 

# class CustomValue(models.Model):
#     custom_title = models.ForeignKey(CustomTitle, on_delete= models.CASCADE)
#     product      = models.ForeignKey(Product, on_delete= models.CASCADE)
#     value        = models.CharField(max_length= 1000)

#     class Meta:
#         db_table = 'company_custom_value' 

class CompanyPhonebook(models.Model):
    company = models.ForeignKey('Company', on_delete= models.CASCADE)
    name    = models.CharField(max_length = 20, blank = True)
    mobile  = models.CharField(max_length = 20, blank = True)
    email   = models.CharField(max_length = 100, blank= True)
    
    class Meta:
        db_table = 'company_phonebook'
