from django.contrib import admin
from .models import Category,Product,ProductVariant,Attribute,AttributeValue,CategoryAttribute,ProductVariantImage,VariantAttribute

# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductVariantImage)
admin.site.register(Attribute),
admin.site.register(AttributeValue),
admin.site.register(CategoryAttribute),
admin.site.register(VariantAttribute)
