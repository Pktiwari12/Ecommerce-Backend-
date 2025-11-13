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
    path("update/product/<int:product_id>/",views.update_product,name='update_product'),
    path("delete/product/<int:product_id>/",views.delete_product,name='delete_product'),
    path("update/varinat/<int:product_id>/<int:variant_id>/",views.update_variant,name='update_variants'),
    path("delete/variant/<int:product_id>/<int:variant_id>/",views.delete_variant,name='delete_variants'),
    path("get/category-path/",views.get_category_path,name='get_category_path'),
]