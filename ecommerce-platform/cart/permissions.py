from rest_framework import permissions
from accounts.models import User

class IsCustomer(permissions.BasePermission):
    message = "Only customer can cart items"

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated or user.role != 'customer':
            return False
        
        return True
    
    