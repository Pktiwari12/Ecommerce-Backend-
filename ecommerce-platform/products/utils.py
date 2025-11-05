from .models import Category

def find_leaf_nodes():
    leaf_nodes = Category.objects.filter(is_leaf=True)
    

