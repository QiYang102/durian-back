from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUserOrReadyOnly(BasePermission):
    def has_permission(self, request, view):
        authenticated = bool(request.user and request.user.is_authenticated)
        readonly = bool(request.method in SAFE_METHODS)
        authenticated_and_readonly = authenticated and readonly

        return bool(
            authenticated_and_readonly or
            request.user.is_staff
        )


class HasUserAccessOrReadyOnly(BasePermission):
    def has_permission(self, request, view):
        authenticated = bool(request.user and request.user.is_authenticated)
        readonly = bool(request.method in SAFE_METHODS)
        authenticated_and_readonly = authenticated and readonly

        return bool(
            authenticated_and_readonly or
            request.user.has_user_access
        )
