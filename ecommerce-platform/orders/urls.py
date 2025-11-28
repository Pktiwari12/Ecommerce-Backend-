from django.urls import path
from . import views

urlpatterns = [
    path("validate-items/",views.validate_items, name="validate_items"),
    path("validate-checkout/",views.validate_checkout,name='validate_checkout'),
    path("initiate-payment/",views.initiate_payment,name='initiate_payment'),
    path("razorpay-webhook/",views.razorpay_webhook,name='razorpay_webhook'),
    path("create-order-cod/",views.create_order_cod,name='create_order_cod'),
    
]