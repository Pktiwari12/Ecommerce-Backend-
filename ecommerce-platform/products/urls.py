from django.urls import path
from . import views

urlpatterns = [
    path("categories/leaf-nodes/",views.nested_category_view, name='nested_category'),
    path("category/<int:category_id>/attributes/",views.category_attribute, name='category_attribute'),
    path("add-product/",views.add_product, name='add_product'),
    path("add-variants/<product_id>/",views.add_variants,name='add_variants'),
    path("get/product/<product_id>/",views.get_product,name='show_product'),
    path("get/products/",views.get_all_products,name='get_all_products'),
    path("vendor/get/products/",views.vendor_get_all_products,name='vendor_get_all_products'),
    path("vendor/get/<product_id>/",views.vendor_get_product,name='vendor_get_product'),
]