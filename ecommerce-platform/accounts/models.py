from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.utils import timezone
# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_active",True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Super User must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Super user must have is_superuser=True")
        
        return self.create_user(email,password, **extra_fields)



class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin_level_1', 'Admin level 1'),
        ('admin_level_2', 'Admin level 2'),
        ('admin_level_3', 'Admin level 3'),
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
    ]
    email = models.EmailField(unique=True, null=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,default='customer')
    username = None
    is_verified = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.email


# model for email verification

class EmailOtp(models.Model):
    email = models.EmailField(unique=True,null=False)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    #otp vaild upto 5 min
    def isExpire(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)
    
    def __str__(self):
        return f"{self.email} verification status = {self.is_verified}"

