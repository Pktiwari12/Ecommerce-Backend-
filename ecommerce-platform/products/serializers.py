from rest_framework import serializers
from .models import Category,Product,ProductVariant,CategoryAttribute,AttributeValue,ProductVariantImage
import json
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
    


class AddVariantSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    # sku = serializers.CharField(max_length=100,required=True)
    adjusted_price = serializers.DecimalField(max_digits=10,decimal_places=2)
    stock = serializers.IntegerField(required=True)

    attribute_and_value = serializers.CharField()
    #     child = serializers.DictField(
    #         child = serializers.IntegerField()
    #     ),required=True
    # )

    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True
    )

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value,is_deleted=False)
            self.context['product'] = product
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist.")
        
        return value
    
    # def validate_sku(self,value):
    #     if ProductVariant.objects.filter(sku=value).exists():
    #         raise serializers.ValidationError("SKU already exists.")
        
    #     return value
    
    def validate_stock(self,value):
        if value < 0:
            raise serializers.ValidationError("Stock can not be negative.")
        return value
    
    def validate_attribute_and_value(self,value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON for attribute_and_value")

        # Ensure it's a list of dicts
        if not isinstance(value, list):
            raise serializers.ValidationError("attribute_and_value must be a list of dicts")
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each item must be a dictionary")
            if 'attribute_id' not in item or 'value_id' not in item:
                raise serializers.ValidationError("attribute_id and value_id are required")
            return value
        if not value:
            raise serializers.ValidationError("Attributes are required.")
        
        product = self.context.get('product')
        try:
            category = product.category.first()
        except Exception as e:
            raise serializers.ValidationError("Unable to find catagory for this product.")
        
        if not category:
            raise serializers.ValidationError("Product has no category.")
        
        allowed_attrs = CategoryAttribute.objects.filter(category=category).values_list('attribute_id',flat=True)

        seen = set()
        for attr in value:
            attr_id = attr.get('attribute_id')
            val_id = attr.get('value_id')

            # required in json format
            if not attr_id or not val_id:
                raise serializers.ValidationError("attribute_id + value_id are required.")
            
            # must be allowed by category
            if attr_id not in allowed_attrs:
                raise serializers.ValidationError(f"Attribute {attr_id} not allowed in this category.")
            
            # must not duplicate attribute
            if attr_id in seen:
                raise serializers.ValidationError(f"Duplicate attribute {attr.id} is not allowed.")
            
            seen.add(attr_id)

            # values must be corresponding to attribute
            if not AttributeValue.objects.filter(id=val_id,attribute_id=attr_id).exists():
                raise serializers.ValidationError(f"Invaild value {val_id} for attribute {attr_id}.")
            
        return value


class ProductUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2,required=True)
    status = serializers.CharField(required=True)

    def validate_status(self,value):
        if not value in ['active', 'inactive']:
            raise serializers.ValidationError("value must be active or inactve.")
        
        return value
    
    def validate_title(self,value):
        product = self.context['product']
        if Product.objects.filter(title=value).exclude(id=product.id).exists():
            raise serializers.ValidationError("Product title must be unique.")
        
        return value
        
        
    def validate_base_price(self,value):
        if value < 0:
            raise serializers.ValidationError("Pricee can not be negative.")
        
        return value



class VariantUpdateSerializer(serializers.Serializer):
    # sku = serializers.CharField(max_length=100,required=True)
    adjusted_price = serializers.DecimalField(max_digits=10,decimal_places=2,required=True)
    stock = serializers.IntegerField(required=True)
    is_active = serializers.BooleanField(required=True)
    deleted_images_id = serializers.CharField(required=False)
    primary_image_id = serializers.IntegerField(required=False)
    primary_image = serializers.ImageField(required=False,allow_null=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True
    )    
    def validate_stock(self,value):
        if value < 0:
            raise serializers.ValidationError("Stock can not be negative.")
        return value

    def validate_primary_image_id(self,value):
        if not value: # no problem if if value == none
            return value
        print("Hello, I am in primary_image field label.")
        if not ProductVariantImage.objects.filter(id=value).exists():
            raise serializers.ValidationError("Image id not found.")
        
        if  ProductVariantImage.objects.filter(id=value,is_primary=False).exists():
            raise serializers.ValidationError("This id is not primary image")
        
        return value
    
    def validate(self,data):
        pid = data.get('primary_image_id')
        pimg = data.get('primary_image')
        print("Hello, I am in data label.")
        if not pid and not pimg:
            raise serializers.ValidationError("Both primary_image_id and primary_image can not be empty.")
        del_img_id = getattr(self,'deleted_images_id',[])
        if pid in del_img_id:
            raise serializers.ValidationError("Deleted_images_id must not have primary_image_id.")
        return data
    
    def validate_deleted_images_id(self,value):
        print("Hey I am here")
        if not value:
            print("value is none initially.")
            return value
        if isinstance(value,str):
            try:
                print("value is string initially.")
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON for deleted_image_id.It must be list.")
            
        if not isinstance(value,list):
            raise serializers.ValidationError("deleted_image_id must be a list.")
        print("value is list initially.")
        self.deleted_images_id = value
        for id in value:
            print(id)
            if not ProductVariantImage.objects.filter(id=id,is_deleted=False).exists():
                raise serializers.ValidationError(f" image id {id} is not found to be deleted. ")
        return value
            




