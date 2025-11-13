from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes,parser_classes
from rest_framework import status
from rest_framework.response import Response
from .utils import (find_leaf_nodes,generate_sku,get_products,
                    generate_one_time_ever_product_name,generate_title_for_deleted_product,
                    generate_sku_for_deleted_variants)
from .serializers import (LeafCategorySerializer,CategoryAttributeValueSerializer,
                          AddProductSerializer,AddVariantSerializer,ProductUpdateSerializer,
                          VariantUpdateSerializer
                          )
from .permissions import IsVendor
from .models import (Category,CategoryAttribute,Attribute,AttributeValue,
                     Product,ProductVariant,VariantAttribute,ProductVariantImage)
from .tasks import delete_product_without_variants # time scheduling based deletion
# for image upload
from rest_framework.parsers import MultiPartParser,FormParser
# from datetime import datetime

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
        const_name = generate_one_time_ever_product_name(serializer.validated_data['title'])
        try:
            product = Product.objects.create(
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                base_price=serializer.validated_data['base_price'],
                const_name=const_name,
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
        sku = generate_sku(product.const_name,attrs)
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
            variant.delete() # rollback
            return Response({
                "message": "Unable to add variant attributes and values.",
                "error": str(e),
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # save images
        try:
            for index,img in enumerate(images):
                print("I am ere")
                alt_text = f"{variant.sku}-Image {index+1}"
                ProductVariantImage.objects.create(
                    product=product,
                    variant=variant,
                    image=img,
                    alt_text=alt_text,
                    is_primary=(index==0) # first image primary
                )   
        except Exception as e:
            variant.delete() # rollback
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
        
@api_view(['GET'])
@permission_classes([])
def get_product(request,product_id):
    try:
        product = Product.objects.prefetch_related(
                "variants__attributes__attribute",
                "variants__attributes__value",
                "variants__images"
            ).filter(id=product_id,is_deleted=False)
    except Exception as e:
        return Response({
            "message": "Unable to find variants of products"
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if not product:
        return Response({
            "message": "Product is not Found."
        },status=status.HTTP_400_BAD_REQUEST)
    
    if product[0].status != 'active':
        return Response({
            "message": "Active product is not found."
        },status=status.HTTP_400_BAD_REQUEST)
    
    data = get_products(request,product)

    if len(data )== 0:
        return Response({
            "message": "Unable to find product details."
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(data,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([])
def get_all_products(request):
    try:
        products = Product.objects.prefetch_related(
                "variants__attributes__attribute",
                "variants__attributes__value",
                "variants__images"
            ).filter(status='active',is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            "message": "Unable to load Products."
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            "message": "Unable to find variants of products"
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    data = get_products(request,products)

    if len(data )== 0:
        return Response({
            "message": "no active product found"
        },status=status.HTTP_200_OK)
    
    return Response(data,status=status.HTTP_200_OK)
    
# for vendor specific
@api_view(['GET'])
@permission_classes([IsVendor])
def vendor_get_product(request,product_id):
    print("I am in sisngl")
    try:
        product = Product.objects.prefetch_related(
                "variants__attributes__attribute",
                "variants__attributes__value",
                "variants__images"
            ).filter(id=product_id,vendor=request.user,is_deleted=False)
    except Exception as e:
        return Response({
            "message": "Unable to find variants of products"
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if not product:
        return Response({
            "message": "Product is not Found."
        },status=status.HTTP_400_BAD_REQUEST)
    
    # if product[0].status != 'active':
    #     return Response({
    #         "message": "Active product is not found."
    #     },status=status.HTTP_400_BAD_REQUEST)
    
    data = get_products(request,product)

    if len(data )== 0:
        return Response({
            "message": "Unable to find product details."
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(data,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsVendor])
def vendor_get_all_products(request):
    print("I am hre")
    try:
        products = Product.objects.prefetch_related(
                "variants__attributes__attribute",
                "variants__attributes__value",
                "variants__images"
            ).filter(vendor=request.user,is_deleted=False)
    except Exception as e:
        print("Error: ",e)
        return Response({
            "message": " to find variants of products"
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if not products:
        return Response({
            "message": "Products not Found."
        },status=status.HTTP_400_BAD_REQUEST)
    
    data = get_products(request,products)
    
    if len(data )== 0:
        return Response({
            "message": "no active product found"
        },status=status.HTTP_200_OK)
    
    return Response(data,status=status.HTTP_200_OK)
    



@api_view(['PUT'])
@permission_classes([IsVendor])
def update_product(request,product_id):
    try:
        product = Product.objects.get(id=product_id,vendor=request.user,is_deleted=False)
    except Product.DoesNotExist:
        return Response({
            "message": "Product not found"
        },status=status.HTTP_404_NOT_FOUND)        


    serializer = ProductUpdateSerializer(data=request.data,context={"product":product})

    if serializer.is_valid():
        try:
            product.status=serializer.validated_data['status']
            product.title=serializer.validated_data['title']
            print(serializer.validated_data['title'])
            print(serializer.validated_data['description'])
            product.description = serializer.validated_data['description']
            product.base_price = serializer.validated_data['base_price']
            product.save()
        except Exception as e:
            return Response({
                "error": str(e)
            },status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "base_price": product.base_price,
            "status": product.status
        },status=status.HTTP_200_OK)

    return Response({
        "message": "Invalid Data",
        "errors": serializer.errors,
    },status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsVendor])
def delete_product(request,product_id):
    try:
        product = Product.objects.get(id=product_id,vendor=request.user,is_deleted=False)
        product.is_deleted = True
        # now = datetime.now()
        # timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        # print(timestamp)
        product.title = generate_title_for_deleted_product(product.title)
        product.save()
    except Product.DoesNotExist:
        return Response({
            "message": "Product not found",
        },status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            "message": "Unable to delete the Product.",
            "error": str(e)
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        "message": "Product deleted successfully",
    },status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsVendor])
@parser_classes([MultiPartParser,FormParser])
def update_variant(request,product_id,variant_id):
    try:
        variant = ProductVariant.objects.get(id=variant_id,is_deleted=False)
    except ProductVariant.DoesNotExist:
        return Response({
            "message": "Variants not found."
        },status=status.HTTP_404_NOT_FOUND)
        
    if not (variant.product.id == product_id and variant.product.vendor.id == request.user.id):
        return Response({
            "message": "Variant not Found"
        },status=status.HTTP_400_BAD_REQUEST)
    
    serializer = VariantUpdateSerializer(data=request.data)
    if serializer.is_valid():
        variant.adjusted_price = serializer.validated_data.get('adjusted_price')
        variant.stock = serializer.validated_data.get('stock')
        variant.is_active = serializer.validated_data.get('is_active')

        if not serializer.validated_data.get('primary_image_id'):
            try:
                print("I am ere")
                alt_text = f"{variant.sku}-Primary-Image"
                prev_primary_img = ProductVariantImage.objects.get(variant=variant,is_primary=True)
                pvi = ProductVariantImage.objects.create(
                    product=variant.product,
                    variant=variant,
                    image=serializer.validated_data.get('primary_image'),
                    alt_text=alt_text,
                    is_primary=True 
                )
                prev_primary_img.is_primary = False
                prev_primary_img.is_deleted = True
                prev_primary_img.save()
                print(f"Primary image id {pvi.id}")
            except Exception as e:
                return Response({
                    "message": "Unable to add primary image.",
                    "error": str(e),
                },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        deleted_image_id = serializer.validated_data.get('deleted_images_id')
        print(deleted_image_id)
        if deleted_image_id:
            print(deleted_image_id)
            for id in deleted_image_id:
                try:
                    del_img = ProductVariantImage.objects.get(id=id,variant=variant)
                    del_img.is_deleted = True
                    del_img.save()
                except ProductVariantImage.DoesNotExist:
                    return Response({
                        "message": "Image id for deletion is not found."
                    },status=status.HTTP_404_NOT_FOUND)
        
        images = serializer.validated_data.get('images',{})
        print(images)
        for img in images:
            alt_text = f"{variant.sku}-Image"
            try:
                ProductVariantImage.objects.create(
                    product=variant.product,
                    variant=variant,
                    image=img,
                    alt_text=alt_text,
                    is_primary=False 
                )
            except Exception as e:
                return Response({
                    "message": "Unable to add images",
                    "error": str(e)
                },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        variant.save()

        return Response({
            "message": "Variant Updated Successfully"
        },status=status.HTTP_200_OK)
    
    return Response({
        "message": "Invaid Data",
        "errors": serializer.errors,
    },status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsVendor])
def delete_variant(request,product_id,variant_id):
    try:
        variant = ProductVariant.objects.get(id=variant_id,is_deleted=False)
    except ProductVariant.DoesNotExist:
        return Response({
            "message": "Variants not found."
        },status=status.HTTP_404_NOT_FOUND)
        
    if not (variant.product.id == product_id and variant.product.vendor.id == request.user.id):
        return Response({
            "message": "Variant not Found"
        },status=status.HTTP_400_BAD_REQUEST)
    
    variant.sku = generate_sku_for_deleted_variants(variant.sku)
    variant.is_deleted = True
    variant.save()

    return Response({
        "message": "Variant is deleted successfully.",
    },status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([])
def get_category_path(request):
    try:
        categories = Category.objects.filter(is_leaf=True)
    except Exception as e:
        return Response({
            "message": "Unable to load attribute"
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    data = []
    for cat in categories:
        data.append({
            "id": cat.id,
            "category_path": cat.get_path()
        })
    
    return Response(data,status=status.HTTP_200_OK)

