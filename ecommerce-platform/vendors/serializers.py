from rest_framework import serializers
from .models import Vendor

class VendorSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.currentUserDefault())
    email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Vendor
        fields = ['id', 
                  'owner', 
                  'email', 
                  'business_name',
                  'phone',
                  'status',
                  'created_at',
                  ]

