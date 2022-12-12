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

# class UserPermission(models.Model):
#     uesr = models.ForeignKey(User, on_delete = models.CASCADE)
#     per1 = models.BooleanField(default = False)
#     per2 = models.BooleanField(default = False)
#     per3 = models.BooleanField(default = False)
    
#     class Meta:
#         db_table = 'user_permission'

# class PermissionGroup(models.Model):
#     title = models.CharField(max_length= 300, default= '그룹 제목')
#     per1 = models.IntegerField(default=0)
#     per2 = models.IntegerField(default=0)
#     per3 = models.IntegerField(default=0)

#     class Meta:
#         db_table = 'permission_group'