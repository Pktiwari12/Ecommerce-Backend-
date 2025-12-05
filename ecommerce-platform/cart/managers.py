from django.db import models, transaction
from decimal import Decimal
from .exceptions import CartError
from products.models import ProductVariant

class CartManager(models.Manager):
    def get_or_create_cart(self,customer):
        cart,created = self.get_or_create(customer=customer)
        return cart
    

class CartItemManager(models.Manager):
    @transaction.atomic
    def add_item(self,cart,variant_id,quantity=1):
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            raise CartError("Variant does not exist.")
        
        if not variant.is_active or variant.is_deleted:
            raise CartError("Variant not available.")
        
        if quantity <= 0:
            raise CartError("Quantity must be positive.")
        
        item,created = self.get_or_create(
            cart=cart,
            product_variant=variant,
            defaults={
                "price": variant.adjusted_price or variant.product.base_price,
                "quantity": quantity,
            }
        )

        if not created:
            item.quantity += quantity
        
        item.save()
        return item
    
    @transaction.atomic
    def update_quantity(self,item,new_quantity):
        if new_quantity <= 0:
            raise CartError("Quantity must be positive")
        
        item.quantity = new_quantity
        item.save()
        return item
    

        
        