from rest_framework.permissions import BasePermission


class IsAuthorOrAdminOnly(BasePermission):
    """Автор или администратор."""

    def has_object_permission(self, request, view, instance):
        return (
            request.user
            and (request.user.is_staff or request.user == instance.author)
        )
