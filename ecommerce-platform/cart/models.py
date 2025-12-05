from django.db import models
from decimal import Decimal
from django.core.exceptions import ValidationError

from accounts.models import User
from products.models import ProductVariant
from .managers import CartManager, CartItemManager
# Create your models here.

class Cart(models.Model):
    """
    One active cart per customer
    """
    customer = models.OneToOneField(User,on_delete=models.CASCADE,related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CartManager()

    def __str__(self):
        return f"Cart({self.customer.email})"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_ammount(self):
        return sum(item.subtotal for item in self.items.all())
    
    
    def save(self, *args, **kwargs):
        if self.customer.role == 'customer':
            super().save(*args,**kwargs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name="items")
    product_variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("cart", "product_variant"))

    def __str__(self):
        return f"{self.product_variant.sku} x {self.quantity}"
    
    objects = CartItemManager()

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive.")
        
        if not self.product_variant.is_active or self.product_variant.is_deleted:
            raise ValidationError("Variant not available for sale.")
        
        return super().clean()
    

    def save(self,*args, **kwargs):
        # this is optional for consistency
        if self.price is None:
            base_price = (
                self.product_variant.adjusted_price
                or self.product_variant.product.base_price
            )
            self.price = Decimal(base_price)

        self.subtotal = Decimal(self.price) * self.quantity
        super().save(*args, **kwargs)





