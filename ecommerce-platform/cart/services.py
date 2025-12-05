from decimal import Decimal
from .models import Cart,CartItem
from .exceptions import CartError


class CartService:
    
    @staticmethod
    def get_cart(customer):
        return Cart.objects.get_or_create_cart(customer)
    
    @staticmethod
    def add_to_cart(customer,variant_id,qty=1):
        cart = CartService.get_cart(customer)
        return CartItem.objects.add_item(cart,variant_id,qty)
    
    @staticmethod
    def update_item(customer,item_id,qty):
        cart = CartService.get_cart(customer)

        try:
            item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            raise CartError("Cart item not found.")
        
        return CartItem.objects.update_quantity(item,qty)
            
        