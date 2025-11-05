from rest_framework import serializers
from .models import Category

class LeafCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    

class AttributeValueSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.CharField()


class AttributeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    input_type = serializers.CharField()
    is_required = serializers.BooleanField()
    values = AttributeValueSerializer(many=True)


class CategoryAttributeValueSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_path = serializers.ListField(child=serializers.CharField())
    attribute = AttributeSerializer(many=True)
    


class AddProductSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_id = serializers.IntegerField(required=True)

    def validate_base_price(self,value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive.")
        return value
    
    def validate_category_id(self,value):
        try: 
            category = Category.objects.get(id=value)
            if not category.is_leaf:
                raise serializers.ValidationError("Category must be only leaf node.")
        except Category.DoesNotExist:
            raise serializers.ValidationError("Enter vaild Category.")
        
        return category
    
