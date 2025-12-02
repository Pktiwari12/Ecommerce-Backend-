from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from .models import Vendor,VendorOnboardingState,VendorID,PickUpAddress,VendorStats
from products.models import Product
from orders.models import OrderItem

# when Vendor Created , then VendorState is created successfully
@receiver(post_save,sender=Vendor)
def create_vendor_state(sender,instance,created,**kwargs):
    if created:
        VendorStats.objects.create(vendor=instance)


@receiver(post_save,sender=Vendor)
def create_onboarding_state(sender,instance,created,**kwargs):
    """
    Singals to automatically create VendorOnboardingState when a Vendor is created.Sets is registered=True
    """
    if created:
        VendorOnboardingState.objects.create(
            vendor=instance,
            is_registered=True
        )



@receiver(post_save,sender=VendorID)
def vendor_document_uploaded(sender,instance,created,**kwargs):
    vendor = instance.vendor

    # check vendor has onboarding state
    if not hasattr(vendor,'state'):
        return
    
    onboarding_state = vendor.state

    if vendor.is_completed:
        return
    
    if not onboarding_state.document_uploaded:
        onboarding_state.document_uploaded = True
        onboarding_state.save()
    
    #checkOnboardingState()


@receiver(post_save,sender=PickUpAddress)
def pickup_address_uploaded(sender,instance,created,**kwargs):
    vendor = instance.vendor

    if not hasattr(vendor,'state'):
        return
    
    onboarding_state = vendor.state

    if vendor.is_completed:
        return
    
    if not onboarding_state.pickup_address:
        onboarding_state.pickup_address = True
        onboarding_state.save()

    # checkOnboardingState()




# Vendor Stats
@receiver(post_save,sender=Product)
def update_product_stats(sender,instance,created,**kwargs):
    print("I am in vendor product stats singal")
    vendor_stats, _ = VendorStats.objects.get_or_create(vendor=instance.vendor.vendor)
    total_products = Product.objects.filter(vendor=instance.vendor,is_deleted=False)
    vendor_stats.not_verified_products = total_products.filter(is_verified=False).count()
    vendor_stats.active_products = total_products.filter(is_verified=True,status='active').count()
    vendor_stats.inactive_products = total_products.filter(is_verified=True,status='inactive').count()
    vendor_stats.save()

@receiver(post_save,sender=OrderItem)
def update_order_stats(sender,instance,created,**kwargs):
    vendor_stats, _ = VendorStats.objects.get_or_create(vendor=instance.vendor)
    total_orders = OrderItem.objects.filter(vendor=instance.vendor)
    vendor_stats.total_order_items = total_orders.count()

    if instance.status == "CLOSED":
        vendor_stats.total_earning += instance.vendor_earning

    vendor_stats.save()

