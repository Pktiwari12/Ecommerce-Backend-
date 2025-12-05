from rest_framework import serializers
from .models import Cart,CartItem


class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    qty = serializers.IntegerField(default=1)
