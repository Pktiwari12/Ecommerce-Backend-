from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin_level_1', 'Admin level 1'),
        ('admin_level_2', 'Admin level 2'),
        ('admin_level_3', 'Admin level 3'),
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
    ]
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,default='customer')
