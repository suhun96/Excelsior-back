from django.db import models

# Create your models here.
class User(models.Model):
    phone       = models.CharField(max_length = 100, blank = False, unique = True)
    name        = models.CharField(max_length = 100, blank = False)
    email       = models.CharField(max_length = 100)
    team        = models.CharField(max_length = 100)
    password    = models.CharField(max_length = 500, blank = False)
    position    = models.CharField(max_length = 50)
    admin       = models.BooleanField(default = False)
    status      = models.BooleanField(default = True)
    created_at  = models.DateTimeField(auto_now_add = True)
    updated_at  = models.DateField(auto_now = True)

    class Meta:
        db_table = 'users'