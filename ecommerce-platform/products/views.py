from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes,parser_classes
from rest_framework import status
from rest_framework.response import Response
from .utils import find_leaf_nodes,generate_sku
from .serializers import (LeafCategorySerializer,CategoryAttributeValueSerializer,
                          AddProductSerializer,AddVariantSerializer
                          )
from .permissions import IsVendor
from .models import (Category,CategoryAttribute,Attribute,AttributeValue,
                     Product,ProductVariant,VariantAttribute,ProductVariantImage)
from .tasks import delete_product_without_variants
# for image upload
from rest_framework.parsers import MultiPartParser,FormParser

# Create your views here.

@api_view(['GET'])
@permission_classes([IsVendor])
def nested_category_view(request):
    leaves = find_leaf_nodes() 
    serializer = LeafCategorySerializer(leaves,many=True)
    return Response(serializer.data,status=status.HTTP_200_OK)

# get attributes for specific attribute
@api_view(['GET'])
@permission_classes([IsVendor])
def category_attribute(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)
    
    if not category.is_leaf:
        return Response({"error": "Category must be leaf node"}, status=400)
    
    # collecting data using select_related and prefetched_related
    attributes_data = []
    mappings = CategoryAttribute.objects.filter(category=category)\
               .select_related('attribute')\
               .prefetch_related('attribute__value')
    
    for mapping in mappings:
        attribute = mapping.attribute # not hit db cause of select_relted
        values = attribute.value.all() # not hit db due to prefectch_related

        attributes_data.append({
            "id": attribute.id,
            "name": attribute.name,
            "input_type": attribute.input_type,
            "is_required": mapping.is_required,
            "values": list(values.values("id","value")) # values = query_set and .values = convert dictionay like object
        })
    
    response_data = {
        "category_id": category.id,
        "category_path": category.get_path(),
        "attribute": attributes_data
    }

    serializer = CategoryAttributeValueSerializer(response_data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsVendor])
def add_product(request):
    serializer = AddProductSerializer(data=request.data)
    if serializer.is_valid():
        category = serializer.validated_data['category_id']
        try:
            product = Product.objects.create(
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                base_price=serializer.validated_data['base_price'],
                # category=serializer.validated_data['category_id'], # this return object
                vendor = request.user,
                status="inactive"
            )
            product.category.add(category) # used in many to many reln
            delete_product_without_variants.apply_async(args=[product.id],countdown=180) # 3 min
        except Exception as e:
            return Response({
                "message": "Unable to add Product.",
                "details": str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "id": product.id,
            "title": product.title,
            "status": product.status,
            "category": category.name
        },status=status.HTTP_201_CREATED)
    
    return Response({
        "message": "Invalid Data",
        "errors": serializer.errors, 
    },status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsVendor])
@parser_classes([MultiPartParser,FormParser])

def add_variants(request,product_id):
    data = request.data.copy()
    data['product_id'] = product_id

    serializer = AddVariantSerializer(data=data)

    if serializer.is_valid():
        product = serializer.context['product']
        # sku = serializer.validated_data['sku']
        stock = serializer.validated_data['stock']
        adj_price = serializer.validated_data['adjusted_price']
        attrs = serializer.validated_data['attribute_and_value']
        images = serializer.validated_data.get('images',{})
        sku = generate_sku(product.title,attrs)
        print(sku)
        if ProductVariant.objects.filter(sku=sku).exists():
            return Response({
                "message": "This Variants for the product is already available."
            },status=status.HTTP_400_BAD_REQUEST)
        # fetch attribute names and values for SKU
        try:
            # create variant
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                adjusted_price=adj_price,
                stock=stock,
                is_active=False
            )
        except Exception as e:
            return Response({
                "message": "Unable to add variant.",
                "error": str(e),
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

        # save attribute combinaions corresponding to variants
        try:
            for attr in attrs:
                VariantAttribute.objects.create(
                    variant=variant,
                    attribute_id=attr['attribute_id'],
                    value_id=attr['value_id']
                )
        except Exception as e:
            return Response({
                "message": "Unable to add variant attributes and values.",
                "error": str(e),
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # save images
        try:
            for index,img in enumerate(images):
                ProductVariantImage.objects.create(
                    product=product,
                    variant=variant,
                    image=img,
                    is_primary=(index==0) # first image primary
                )   
        except Exception as e:
            return Response({
                "message": "Unable to add variant.",
                "error": str(e),
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        product.status = 'pending'
        product.save()

        return Response({
            "message": "Variant added Successfully.",
            "variant_id": variant.id
        },status=status.HTTP_201_CREATED)
        

    
    return Response({
        "message": "Invalid Data",
        "errors": serializer.errors,
    },status=status.HTTP_400_BAD_REQUEST)
