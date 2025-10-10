from django.urls import path
from . import views

urlpatterns = [
    path('request-otp/', views.email_otp_request, name='request_otp'),
    path('verify-email/', views.email_verify, name='email_verify'),
]