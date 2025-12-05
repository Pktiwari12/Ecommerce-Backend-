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
    
    # def validate_shipping_email(self,value):
    #     if not ( self.context.get('customer') or value) :
    #         raise serializers.ValidationError("Guest User must have provide email.")
        
    #     return value

        

class InitiatePaymentSerializer(serializers.Serializer):
    checkout_session_id = serializers.UUIDField()
        

class CreateCodSerializer(serializers.Serializer):
    checkout_session_id = serializers.UUIDField()


class CustomerOrderItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(source="id")
    product_variant_id = serializers.IntegerField(source="product_variant.id")
    product_id = serializers.IntegerField(source="product_variant.product.id")
    quantity = serializers.IntegerField()
    product_name = serializers.CharField(source="product_variant.product.title")
    sku = serializers.CharField(source="product_variant.sku")
    price = serializers.DecimalField(max_digits=12,decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=12,decimal_places=2)
    status = serializers.CharField()
    delivered_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    variant_primary_image = serializers.SerializerMethodField()

    def get_variant_primary_image(self,obj):
        request = self.context.get('request')
        print(request)
        img = obj.product_variant.images.filter(is_primary=True,is_deleted=False).first()

        if img:
            return {
                "image": request.build_absolute_uri(img.image.url),
                "alt_text": img.alt_text

            }
        return None

class CustomerOrderListSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    status = serializers.CharField()
    payment_method = serializers.CharField()
    payment_status = serializers.CharField(allow_null=True, allow_blank=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    is_refundable = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    shipping = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    def get_shipping(self,obj):
        return {
            "name": obj.shipping_name,
            "phone": obj.shipping_phone,
            "email": obj.shipping_email,
            "address_1": obj.shipping_address_1,
            "address_2": obj.shipping_address_2,
            "city": obj.shipping_city,
            "state": obj.shipping_state,
            "pincode": obj.shipping_pincode
        }
    def get_items(self,obj):
        return CustomerOrderItemSerializer(obj.items.all(),many=True,context=self.context).data
    

class VendorOrderItemSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField(source="id")
    product_variant_id = serializers.IntegerField(source="product_variant.id")
    product_id = serializers.IntegerField(source="product_variant.product.id")
    product_name = serializers.CharField(source="product_variant.product.title")
    sku = serializers.CharField(source="product_variant.sku")
    
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    tax_amount = serializers.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    vendor_earning = serializers.DecimalField(max_digits=12, decimal_places=2)
    refunded_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    status = serializers.CharField()
    tracking_number = serializers.CharField(allow_null=True)
    courier_name = serializers.CharField(allow_null=True)
    metadata = serializers.JSONField()
    
    delivered_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    
    variant_primary_image = serializers.SerializerMethodField()
    
    def get_variant_primary_image(self, obj):
        request = self.context.get("request")
        img = obj.product_variant.images.filter(is_primary=True, is_deleted=False).first()
        if img and request:
            return {
                "image": request.build_absolute_uri(img.image.url),
                "alt_text": img.alt_text
            }
        return None


class VendorOrderListSerializer(serializers.Serializer):
    # order_number = serializers.CharField(source="order.order_number")
    order_number = serializers.CharField()
    payment_method = serializers.CharField()
    payment_status = serializers.CharField()
    total = serializers.DecimalField( max_digits=12, decimal_places=2)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateField()
    
    shipping = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    
    def get_shipping(self, obj):
        order = obj
        return {
            "name": order.shipping_name,
            "phone": order.shipping_phone,
            "email": order.shipping_email,
            "address_1": order.shipping_address_1,
            "address_2": order.shipping_address_2,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "pincode": order.shipping_pincode
        }
    
    def get_items(self, obj):
        # obj is an OrderItem instance, filter all items of this vendor for the same order
        # order_items = obj.order.items.filter(vendor=obj.vendor)
        order_items = obj.items.all()
        return VendorOrderItemSerializer(order_items, many=True, context=self.context).data

    
