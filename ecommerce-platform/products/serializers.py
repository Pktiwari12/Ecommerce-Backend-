from rest_framework import serializers

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
    
