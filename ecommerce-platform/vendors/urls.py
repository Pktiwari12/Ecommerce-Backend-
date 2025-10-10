from django.urls import path
from . import views

urlpatterns = [
#     path('sign-up/', views.sign_up, name="sign_up"),
      path('register/', views.register_vendor, name='vendor_register'),
]