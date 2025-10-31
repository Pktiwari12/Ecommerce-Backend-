from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-email/', views.email_verify, name='email_verify'),
    path('request-otp/',views.request_otp,name="request_otp"),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view, name='logout' ),
    path('forgot-password/',views.forgot_password,name='forgot_password'),
]       