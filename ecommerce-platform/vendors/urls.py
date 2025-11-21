from django.urls import path
from . import views

urlpatterns = [
#     path('sign-up/', views.sign_up, name="sign_up"),
      path('register/email/otp/', views.vendor_register_email_otp, name='vendor_register_email_otp'),
      path('register/email/verify/', views.vendor_verify_email_otp, name='vendor_verify_email_otp'),
      path('register/phone/otp/',views.vendor_register_mobile_otp,name='vendor_register_mobile_otp'),
      path('register/phone/verify/',views.vendor_verify_mobile_otp, name='verify_mobile_otp'),
      path('upload/document/',views.upload_vendor_doc,name='upload_vendor_doc'),
      path('add/pickup-address/',views.add_pickup_address,name='add_pickup_address'),
      path('register/',views.register_vendor, name='register_vendor'),
      path('login/',views.vendor_login,name="vendor_login"),
      path('onboarding/state/',views.vendor_onboarding_state, name='vendor_onboarding_state'),
]