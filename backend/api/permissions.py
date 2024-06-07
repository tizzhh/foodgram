from rest_framework import permissions
from rest_framework.exceptions import NotFound


class IsAuthorOrSuperuser(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and (request.user.is_superuser or request.user == obj.author)
        )


class IsAuthOrSuperuserOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and (request.user.is_superuser or request.user == obj.author)
        )
