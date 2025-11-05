from django.urls import path
from . import views

urlpatterns = [
    path("categories/leaf-nodes/",views.nested_category_view, name='nested_category'),
    path("category/<int:category_id>/attributes/",views.category_attribute, name='category_attribute'),
    path("add-product/",views.add_product, name='add_product'),
]