from rest_framework import permissions

class IsOnVerdingVendor(permissions.BasePermission):
    message = "Only vendor with incomplete onboarding status is allowed."

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated or user.role != 'vendor':
            return False
        
        vendor = getattr(user, "vendor", None)
        
        if vendor is None:
            return False
        
        return not vendor.is_completed # only those who not finish onboarding.

# only registered vendor Whether onboarded or onboarding
class IsVendor(permissions.BasePermission):
    message = "Only vendors can access"

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated or user.role != 'vendor':
            return False
        
        return True