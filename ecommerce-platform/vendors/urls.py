from django.urls import path
from . import views

urlpatterns = [
#     path('sign-up/', views.sign_up, name="sign_up"),
      path('request-otp/', views.vendor_register_otp, name='vendor_register_otp'),
      path('verify-otp/', views.vendor_verify_otp, name='vendor_verify_otp'),
      path('request/mobile-otp/',views.request_mobile_otp,name='request_mobile_otp'),
      path('verify/mobile-otp/',views.verify_mobile_otp, name='verify_mobile_otp'),
      path('register/',views.register_vendor, name='register_vendor')
]