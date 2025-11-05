from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .utils import find_leaf_nodes
from .serializers import LeafCategorySerializer,CategoryAttributeValueSerializer
from .permissions import IsVendor
from .models import Category,CategoryAttribute,Attribute,AttributeValue

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


    
