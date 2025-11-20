from .models import Category,AttributeValue,Product
from datetime import datetime

def find_leaf_nodes():
    leaf_nodes = Category.objects.filter(is_leaf=True)
    return leaf_nodes

def generate_sku(str,attribute_value):
    product_title = str.lower().replace(' ','-')
    attr_list = []
    print(attribute_value)
    for attr in attribute_value:
        try:
            print(attr)
            obj = AttributeValue.objects.get(id=attr['value_id'])
            print(obj)
            attr_name = obj.attribute.name
            print(obj)
            attr_value = obj.value
            print(obj)
            attr_list.append({
                "attribute_name": attr_name,
                "attribute_value": attr_value
            })
            
        except Exception as e:
            # print("I am in exceptioon.")
            return None
    attribute_part = "-".join(f"{a['attribute_name'].lower()}-{a['attribute_value'].lower()}" for a in attr_list)
        
    return f"{product_title}@{attribute_part}"

def generate_one_time_ever_product_name(title):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    pt = title.lower().replace(' ','-')
    return f"{pt}_{timestamp}"


def get_products(request,products):
    # try:
    #     if(not for_all):
    #         # get only one product. ignore var name
    #         products = Product.objects.prefetch_related(
    #             "variants__attributes__attribute",
    #             "variants__attributes__value",
    #             "variants__images"
    #         ).filter(id=product_id) 
    #     else: 
    #         products = Product.objects.prefetch_related(
    #             "variants__attributes__attribute",
    #             "variants__attributes__value",
    #             "variants__images"
    #         ).filter(status='active')

    # except Product.DoesNotExist:
    #     return None
    # except Exception as e:
    #     return -1           # -1 indicates unable to find other table details related to  product.
    
    # if not products:
    #     return 0
    
    data = []
    for product in products:
        category = list(product.category.all())[0]
        category_id = category.id
        print(category_id)

        product_data = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "base_price": product.base_price,
            "status": product.status,
            "category_id": category_id,
            "category_path": category.get_path(),
            "variants": []
        }
        for variant in product.variants.filter(is_deleted=False):
            product_data["variants"].append({
                "id": variant.id,
                "name": variant.sku,
                "adjusted_price": variant.adjusted_price,
                "stock": variant.stock,
                "is_active": variant.is_active,
                "attributes": [
                    {
                        "attribute": attr.attribute.name,
                        "value": attr.value.value
                    }for attr in variant.attributes.all()
                ],
                "images": [
                    {
                        "id": img.id,
                        "image": request.build_absolute_uri(img.image.url),
                        "alt_text": img.alt_text,
                        "is_primary": img.is_primary
                    } for img in variant.images.filter(is_deleted=False)
                    
                ]
            })
        data.append(product_data)
    return data
    

def generate_sku_for_deleted_variants(sku):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"{sku}_{timestamp}"
    
def generate_title_for_deleted_product(title):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"{title} {timestamp}"


