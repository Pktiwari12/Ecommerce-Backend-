from django.contrib import admin
from .models import (Vendor,PickUpAddress,VendorEmailOtp,
                     VendorMobileOtp,VendorID)
# Register your models here.
admin.site.register(Vendor)
admin.site.register(VendorEmailOtp)
admin.site.register(PickUpAddress)
admin.site.register(VendorMobileOtp)
admin.site.register(VendorID)
