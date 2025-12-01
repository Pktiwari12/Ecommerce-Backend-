from rest_framework import permissions

class IsApprovedVendor(permissions.BasePermission):
    message = "You are not approved venodr."

    def has_permission(self, request, view):
        user = request.user

        if not (user.is_authenticated and user.role == 'vendor'):
            return False
        
        vendor = getattr(user,'vendor', None)

        if not vendor:
            return False
        
        #only approved vendor is allowed to get orders
        if vendor.is_completed and vendor.status == 'APPROVED':
            return True
        
        return False
        
        # # These vendors not allowed to add a product
        # if vendor.status in ['REJECTED','SUSPENDED']:
        #     return False
        
        # onboarding_state = getattr(vendor,'state',None)
        # if not onboarding_state:
        #     return False
        
        # if not (onboarding_state.is_registered and
        #     onboarding_state.document_uploaded and
        #     onboarding_state.pickup_address):
            
        #     return False

             
        

        # # Onboarding Vendor can add only 5 proudct
        # product_count = Product.objects.filter(vendor=user).count()
        # return product_count < 5 # only 5 proudcts allowed


    

