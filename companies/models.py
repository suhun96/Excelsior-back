from django.db import models

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

class CompanyEtcTitle(models.Model):
    title  = models.CharField(max_length=100, blank = False)
    status = models.BooleanField(default = False)

    class Meta:
        db_table = 'company_etc_title'

class CompanyEtcDesc(models.Model):
    company = models.ForeignKey('Company', on_delete= models.CASCADE)
    company_etc_title = models.ForeignKey('CompanyEtcTitle', on_delete= models.CASCADE)
    contents = models.CharField(max_length = 700) 
    
    class Meta:
        db_table = 'company_etc_desc'


class CompanyPhonebook(models.Model):
    company = models.ForeignKey('Company', on_delete= models.CASCADE)
    name    = models.CharField(max_length = 20, blank = True)
    mobile  = models.CharField(max_length = 20, blank = True)
    email   = models.CharField(max_length = 100, blank= True)
    
    class Meta:
        db_table = 'company_phonebook'
