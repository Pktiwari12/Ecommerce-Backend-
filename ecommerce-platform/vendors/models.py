from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
# Create your models here.
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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    seller_name = models.CharField(max_length=250) # like Stationary and etc
    phone = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default="DRAFT")
    gst = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.seller_name

