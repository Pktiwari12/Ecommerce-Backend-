# cart/urls.py
from django.urls import path
from .views import (
    get_cart,
    add_to_cart,
    update_cart_item,
    remove_cart_item,
    clear_cart,
    cart_summary,
)

urlpatterns = [
    path("", get_cart, name="get-cart"),
    path("items/", add_to_cart, name="add-to-cart"),
    path("items/<int:item_id>/", update_cart_item, name="update-cart-item"),
    path("items/<int:item_id>/remove/", remove_cart_item, name="remove-cart-item"),
    path("clear/", clear_cart, name="clear-cart"),
    path("summary/", cart_summary, name="cart-summary"),
]



# cart/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem
from products.models import ProductVariant


class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(source='product_variant.id')
    product_title = serializers.CharField(source='product_variant.product.title', read_only=True)
    sku = serializers.CharField(source='product_variant.sku', read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant_id",
            "product_title",
            "sku",
            "price",
            "quantity",
            "subtotal",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "total_items",
            "total_amount",
        ]


# --- INPUT SERIALIZERS ---

class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)


class UpdateQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField()





# cart/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services import CartService
from .exceptions import CartError
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateQuantitySerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart = CartService.get_cart(request.user)
    return Response(CartSerializer(cart).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    serializer = AddToCartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        item = CartService.add_to_cart(
            customer=request.user,
            variant_id=serializer.validated_data["variant_id"],
            qty=serializer.validated_data["quantity"],
        )
    except CartError as e:
        return Response({"error": str(e)}, status=400)

    return Response(CartItemSerializer(item).data, status=201)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    serializer = UpdateQuantitySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        item = CartService.update_item(
            customer=request.user,
            item_id=item_id,
            qty=serializer.validated_data["quantity"]
        )
    except CartError as e:
        return Response({"error": str(e)}, status=400)

    return Response(CartItemSerializer(item).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    try:
        CartService.remove_item(
            customer=request.user,
            item_id=item_id
        )
    except CartError as e:
        return Response({"error": str(e)}, status=400)

    return Response({"message": "Item removed successfully"})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    CartService.clear_cart(request.user)
    return Response({"message": "Cart cleared"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_summary(request):
    summary = CartService.get_summary(request.user)
    return Response(summary)



# manager.py
from django.db import models, transaction
from decimal import Decimal
from .exceptions import CartError
from products.models import ProductVariant


class CartManager(models.Manager):
    def get_or_create_cart(self, customer):
        cart, created = self.get_or_create(customer=customer)
        return cart


class CartItemManager(models.Manager):

    @transaction.atomic
    def add_item(self, cart, variant_id, quantity=1):
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            raise CartError("Variant does not exist.")

        if not variant.is_active or variant.is_deleted:
            raise CartError("Variant not available.")

        if quantity <= 0:
            raise CartError("Quantity must be positive.")

        item, created = self.get_or_create(
            cart=cart,
            product_variant=variant,
            defaults={
                "price": variant.adjusted_price or variant.product.base_price,
                "quantity": quantity,
            },
        )

        if not created:
            item.quantity += quantity

        item.save()
        return item

    @transaction.atomic
    def update_quantity(self, item, new_quantity):
        if new_quantity <= 0:
            raise CartError("Quantity must be positive.")

        item.quantity = new_quantity
        item.save()
        return item

    @transaction.atomic
    def remove_item(self, item):
        item.delete()



# service.py
from decimal import Decimal
from .models import Cart, CartItem
from .exceptions import CartError


class CartService:

    @staticmethod
    def get_cart(customer):
        return Cart.objects.get_or_create_cart(customer)

    @staticmethod
    def add_to_cart(customer, variant_id, qty=1):
        cart = CartService.get_cart(customer)
        return CartItem.objects.add_item(cart, variant_id, qty)

    @staticmethod
    def update_item(customer, item_id, qty):
        cart = CartService.get_cart(customer)

        try:
            item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            raise CartError("Cart item not found.")

        return CartItem.objects.update_quantity(item, qty)

    @staticmethod
    def remove_item(customer, item_id):
        cart = CartService.get_cart(customer)

        try:
            item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            raise CartError("Cart item not found.")

        CartItem.objects.remove_item(item)

    @staticmethod
    def clear_cart(customer):
        cart = CartService.get_cart(customer)
        cart.items.all().delete()

    @staticmethod
    def get_summary(customer):
        cart = CartService.get_cart(customer)
        return {
            "items": cart.total_items,
            "amount": cart.total_amount,
        }
