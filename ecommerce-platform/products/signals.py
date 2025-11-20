from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from .models import ProductVariant
from vendors.models import VendorOnboardingState


@receiver(post_save,sender=ProductVariant)
def update_product_variant_status_true(sender,instance,created,**kwargs):
    # print("I am in signal")
    if not created:
        return
    
    vendor = instance.product.vendor

    vendor_obj = getattr(vendor,'vendor',None)
    if not vendor_obj:
        return 
    
    
    onboarding_state = getattr(vendor_obj,'state',None)

    if not onboarding_state:
        return 
    
    totlal_varinats = ProductVariant.objects.filter(product__vendor=vendor,is_deleted=False).count()

    # update only if vendor has >= 1 vairant
    if totlal_varinats > 0 and not onboarding_state.product_variant:
        onboarding_state.product_variant = True
        # print(vendor_obj.is_completed)
        vendor_obj.is_completed = True
        # print(vendor_obj.is_completed)
        onboarding_state.save()
        vendor_obj.save()
        return
    
    # update only vendor has 0 variants
    if totlal_varinats == 0 and  onboarding_state.product_variant:
        onboarding_state.product_variant = False
        # print(vendor_obj.is_completed)
        vendor_obj.is_completed = False
        # print(vendor_obj.is_completed)
        onboarding_state.save()
        vendor_obj.save()
        return

    
    

# @receiver(post_delete,sender=ProductVariant)
# def update_product_variant_status_false(sender,instance,**kwargs):

#     vendor = instance.product.vendor

#     vendor_obj = getattr(vendor,'vendor',None)

    
#     if not vendor_obj:
#         return
    
#     if  vendor_obj.status == 'APPROVED':
#         return 
    
#     if not vendor_obj.is_completed:
#         return 
    
#     onboarding_state = getattr(vendor_obj,'state',None)
#     if not onboarding_state:
#         return 
    
#     total_variants = ProductVariant.objects.filter(product__vendor=vendor).count()

#     if total_variants == 0 and  onboarding_state.product_variant:
#         onboarding_state.product_variant = False
#         vendor_obj.is_completed = False
#         onboarding_state.save()
#         vendor_obj.save()

    