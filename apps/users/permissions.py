from rest_framework.permissions import BasePermission, SAFE_METHODS

class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin
    

class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        
        # for other
        if request.method in SAFE_METHODS and request.user.is_authenticated:
            return True
        # for admin
        return request.user and request.user.is_authenticated and request.user.is_admin
