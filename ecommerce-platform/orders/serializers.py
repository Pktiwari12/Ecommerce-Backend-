from rest_framework import serializers
import json

class ItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1)


class ValidateItemSerializer(serializers.Serializer):
    # items_with_qty = serializers.ListField(
    #     child=ItemSerializer()
    # )
    items_with_qty = ItemSerializer(many=True)

    def validate_items_with_qty(self,value):
        if not value:
            raise serializers.ValidationError("items with quantity is required.")
        
        if len(value) <= 0:
            raise serializers.ValidationError("This field can not be empty.")
        return value


class CheckoutValidateSerializer(serializers.Serializer):
    items_with_qty = ItemSerializer(many=True)
    shipping_name = serializers.CharField()
    shipping_phone = serializers.CharField()
    shipping_email = serializers.EmailField(required=False)
    shipping_address_1 = serializers.CharField()
    shipping_address_2 = serializers.CharField(required=False)
    shipping_city = serializers.CharField()
    shipping_state = serializers.CharField()
    shipping_pincode = serializers.CharField()
    payment_choices = ["Cash_On_Delivery", "Online_Mode"]
    payment_method = serializers.CharField()
    def validate_items_with_qty(self,value):
        if not value:
            raise serializers.ValidationError("items with quantity is required.")
        
        if len(value) <= 0:
            raise serializers.ValidationError("This field can not be empty.")
        return value

    def validate_shipping_phone(self,value):
        if len(value) != 10:
            raise serializers.ValidationError("Only ten digits allowed.")
        
        if not value.isdigit():
            raise serializers.ValidationError("Only numeric values is allowed.")
        
        if ' ' in value or '\t' in value  or '\n' in value:
            raise serializers.ValidationError("Invalid mobile number.")
        
        return value
    
    def validate_shipping_pincode(self,value):
        if len(value) != 6:
            raise serializers.ValidationError("Enter valid pincode.")
        return value
        
    
    def validate_payment_method(self,value):
        if value not in self.payment_choices:
            raise serializers.ValidationError("Select only one option in (1.Cash_On_Delivery, 2.Online_Mode)")
        return value
        

class InitiatePaymentSerializer(serializers.Serializer):
    checkout_session_id = serializers.UUIDField()
        

class CreateCodSerializer(serializers.Serializer):
    checkout_session_id = serializers.UUIDField()