from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cart
from accounts.models import User

@receiver(post_save,sender=User)
def create_cart(sender,instance,created,**kwargs):
    if instance.is_verified and instance.role == 'customer':
        Cart.objects.get_or_create(customer=instance)
