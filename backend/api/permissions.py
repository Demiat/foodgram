from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Для автора, иначе только просмотр."""

    def has_permission(self, request, view):
        """Задает общие разрешения на уровне представления."""
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, recipe):
        """Задает конкретные разрешения на уровне доступа к объекту."""
        return (
            request.method in SAFE_METHODS
            or recipe.author == request.user
        )
