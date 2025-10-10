from rest_framework import serializers
from accounts.models import User
from .models import Vendor


class VendorRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=255)
    seller_name = serializers.CharField(max_length=255)
    gst = serializers.CharField(max_length=15)
    # address = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_gst_number(self, value):
        if len(value) != 15:
            raise serializers.ValidationError("GST number must be 15 characters long.")
        return value

    def create(self, validated_data):
        user_data = {
            "email": validated_data["email"],
            "first_name": validated_data["first_name"],
            "role": "VENDOR"
        }

        vendor_data = {
            "seller_name": validated_data["seller_name"],
            "gst": validated_data["gst"],
            # "address": validated_data["address"]
        }

        # Create User
        user = User.objects.create(**user_data)
        user.set_password(validated_data["password"])
        user.save()

        # Create Vendor linked to that user
        vendor = Vendor.objects.create(owner=user, **vendor_data)

        return vendor
