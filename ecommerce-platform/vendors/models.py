from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
# Create your models here.

def signeture_image_upload_path(instance,filename):
    # extention

    ext = filename.split('.')[-1]
    # print("I am in method")
    seller_name = instance.vendor.seller_name
    filename = f"{instance.alt_text_signeture}.{ext}"
    print("I am in end of method.")
    print(filename)
    return f"venodrs/{seller_name}/{filename}"

def gst_certificate_upload_path(instance,filename):
    # extention

    ext = filename.split('.')[-1]
    # print("I am in method")
    seller_name = instance.vendor.seller_name
    filename = f"{instance.alt_text_gst_certificate}.{ext}"
    print("I am in end of method.")
    print(filename)
    return f"vendors/{seller_name}/{filename}"


# these are unnecessary if we will be use catche
class VendorEmailOtp(models.Model):
    business_email = models.EmailField(unique=True,blank=False)
    otp = models.CharField(max_length=6)
    # used first time only
    isUsed = models.BooleanField(default=False)
    # created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    #otp vaild upto 5 min
    def isExpire(self,t):
        return timezone.now() > self.updated_at + timezone.timedelta(minutes=t)
    
    def __str__(self):
        return f"{self.business_email} :  {self.otp}"



class VendorMobileOtp(models.Model):
    business_email = models.EmailField(blank=False,null=False)
    phone = models.CharField(blank=False,null=False)
    otp = models.CharField(max_length=6)
    # used first time only
    isUsed = models.BooleanField(default=False)
    # created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    #otp vaild upto 5 min

    class Meta:
        unique_together = (('business_email','phone'),)
    def isExpire(self,t):
        return timezone.now() > self.updated_at + timezone.timedelta(minutes=t)
    
    def __str__(self):
        return f"{self.phone} :  {self.otp}"


class Vendor(models.Model):
    STATUS = [
        ("DRAFT", "Draft"),
        ("PENDING_KYC", "Pending KYC"),
        ("IN_REVIEW", "In Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("SUSPENDED", "Suspended"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='vendor')
    # identity
    full_name = models.CharField(max_length=250)
    seller_name = models.CharField(max_length=250) # like Stationary and etc
    business_email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10,unique=True)
    
    # status & Metadata
    is_completed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS, default="DRAFT")
    is_active = models.BooleanField(default=True)
    remarks= models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.seller_name

class PickUpAddress(models.Model):
    vendor = models.OneToOneField(Vendor,on_delete=models.CASCADE,related_name='address')
    # vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE,related_name='pickup_address')
    address_line_1 = models.CharField(max_length=300,blank=False,null=False)
    address_line_2 = models.CharField(max_length=300,blank=True,null=True)
    city = models.CharField(max_length=100,blank=False,null=False)
    state = models.CharField(max_length=100,blank=False,null=False)
    pincode = models.CharField(max_length=10,blank=False,null=False)

    # these can be filled by exernal api
    lattitude = models.DecimalField(max_digits=9,decimal_places=9,null=True,blank=True)
    longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class VendorID(models.Model):
    vendor = models.OneToOneField(Vendor,on_delete=models.CASCADE,related_name='gst_docs')
    gst = models.CharField(max_length=15,unique=True)
    # pan_number = models.CharField(max_length=10,blank=True,null=True)
    signeture = models.ImageField(upload_to=signeture_image_upload_path)
    alt_text_signeture = models.CharField(max_length=200,blank=True,null=True)
    gst_certificate = models.ImageField(upload_to=gst_certificate_upload_path)
    alt_text_gst_certificate = models.CharField(max_length=200,blank=True,null=True)
    verified_at_user_level = models.BooleanField(default=False)  # To verify Use Govt Pan API.
    verified_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    

class VendorOnboardingState(models.Model):
    vendor = models.OneToOneField(Vendor,on_delete=models.CASCADE, related_name='state')
    is_registered = models.BooleanField(default=False)
    document_uploaded = models.BooleanField(default=False)
    pickup_address = models.BooleanField(default=False)
    product_variant = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vendor.seller_name} onboarding state "