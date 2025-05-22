from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Для автора, иначе только просмотр."""

    def has_object_permission(self, request, view, recipe):
        """Задает конкретные разрешения на уровне доступа к объекту."""
        return (
            request.method in SAFE_METHODS
            or recipe.author == request.user
        )
