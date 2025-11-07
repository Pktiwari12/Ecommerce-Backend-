from .models import Category,AttributeValue

def find_leaf_nodes():
    leaf_nodes = Category.objects.filter(is_leaf=True)

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
            return None
    attribute_part = "-".join(f"{a['attribute_name'].lower()}-{a['attribute_value'].lower()}" for a in attr_list)
        
    return f"{product_title}-{attribute_part}"
        

    

