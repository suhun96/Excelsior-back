from email.policy import default
from django.db import models

# Create your models here.
class User(models.Model):
    phone       = models.IntegerField(blank = False, unique = True)
    name        = models.CharField(max_length = 100, blank = False)
    password    = models.CharField(max_length = 50, blank = False)
    position    = models.CharField(max_length = 50, blank = False)
    admin       = models.BooleanField(default = False)
    status      = models.BooleanField(default = True)
    created_at  = models.DateTimeField(auto_now_add = True)
    updated_at  = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'users'