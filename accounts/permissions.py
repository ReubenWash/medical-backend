from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'patient')


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        owner = getattr(obj, 'patient', None) or getattr(obj, 'user', None)
        return owner == request.user


class IsAdminOrReadOnly(BasePermission):
    """Anyone can read (GET/HEAD/OPTIONS). Only admins can write."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # Public read access — no login required
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')