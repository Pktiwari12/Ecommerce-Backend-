from rest_framework import permissions
from products.models import Product
class IsVendor(permissions.BasePermission):
    message = "Only onboarded vendor can access."

    def has_permission(self,request,view):
        user = request.user

        if not user.is_authenticated or user.role != 'vendor':
            return False
        
        # vendor = getattr(user,'vendor', None)

        # if vendor is None:
        #     return False
        
        return True
    


class CanAddProduct(permissions.BasePermission):
    message = "You are not allowed to add product"

    def has_permission(self, request, view):
        user = request.user

        if not (user.is_authenticated and user.role == 'vendor'):
            return False
        
        vendor = getattr(user,'vendor', None)

        if not vendor:
            return False
        
        #Onboarded Vendor can add unlimited prouduct
        if vendor.is_completed and vendor.status == 'APPROVED':
            return True
        
        # These vendors not allowed to add a product
        if vendor.status in ['REJECTED','SUSPENDED']:
            return False
        
        onboarding_state = getattr(vendor,'state',None)
        if not onboarding_state:
            return False
        
        if not (onboarding_state.is_registered and
            onboarding_state.document_uploaded and
            onboarding_state.pickup_address):
            
            return False

             
        

        # Onboarding Vendor can add only 5 proudct
        product_count = Product.objects.filter(vendor=user).count()
        return product_count < 5 # only 5 proudcts allowed


    

