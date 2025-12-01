from django.urls import path
from . import views

urlpatterns = [
    path("validate-items/",views.validate_items, name="validate_items"),
    path("validate-checkout/",views.validate_checkout,name='validate_checkout'),
    path("initiate-payment/",views.initiate_payment,name='initiate_payment'),
    path("razorpay-webhook/",views.razorpay_webhook,name='razorpay_webhook'),
    path("create-order-cod/",views.create_order_cod,name='create_order_cod'),
    path("get-all/",views.customer_get_orders,name='customer_get_orders'),
    path("get/<str:order_number>/",views.customer_get_specific_order,name='customer_get_specific order.'), # ignore
    path("vendor-get-all/",views.vendor_get_orders,name='customer_get_specific order.'),
    path("vendor-get/<order_item_id>/",views.vendor_get_specific_order,name='customer_get_specific order.'), # ignore
    
    
    
]