from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from .permissions import IsCustomer
from .serializers import AddToCartSerializer
from .services import CartService
from .exceptions import CartError
from products.models import ProductVariant,ProductVariantImage
# Create your views here.

@api_view(['POST'])
@permission_classes([IsCustomer])
def add_to_cart(request):
    serializer = AddToCartSerializer(data=request.data)

    if serializer.is_valid():
        try:
            item = CartService.add_to_cart(
                customer=request.user,
                variant_id=serializer.validated_data.get('variant_id'),
                qty=serializer.validated_data.get("qty")

            )
        except CartError as e:
            return Response({
                "error": str(e)
            },status=400)
        variant = item.product_variant
        images = variant.images.filter(is_primary=True,is_deleted=False)
        img_url = ""
        if images.exists():
            img_url = request.build_absolute_uri(images.first().image.url)
        

        return Response({
            "product_id": item.product_variant.product.id,
            "variant_id": item.product_variant.id,
            "product_name": variant.product.title,
            "quantity": item.quantity,
            "price": item.price,
            "subtotal": item.subtotal,
            "sku": item.product_variant.sku,
            "image": img_url
        },status=201)
    
    return Response({
        "message": "Invalid Data",
        "errors": serializer.errors
    },status=400)


@api_view(['POST'])
@permission_classes([IsCustomer])
def get_cart(request):
    pass


