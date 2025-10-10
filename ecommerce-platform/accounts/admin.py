from django.contrib import admin
from .models import User,EmailOtp
# Register your models here.
admin.site.register(User)
admin.site.register(EmailOtp)