from rest_framework import permissions

class IsVendor(permissions.BasePermission):
    message = "Only vendors can upload products."

    def has_permission(self,request,view):
        return request.user.is_authenticated and request.user.role=='vendor'