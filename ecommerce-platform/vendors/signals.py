from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vendor,VendorOnboardingState,VendorID,PickUpAddress

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


