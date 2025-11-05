from celery import shared_task
from .models import Product

@shared_task
def delete_product_without_variants(product_id):

    """
    Deletes products which are inactive and have no variants
    and were created more than 30 minutes ago.
    """
    try:
        product = Product.objects.get(id=product_id)
        if not product.variants.exists():
            product.delete()
            return f"product {product_id} deleted (no variants added)."
        else:
            product.status = 'pending'
            product.save()
            return f"Product {product_id} has variants. Not Deleted."
    except Product.DoesNotExist:
        return f"Product {product_id} does not exist."

