from rest_framework.serializers import ModelSerializer

import users.models as mod
import users.validators as valid


class UserSerializer(ModelSerializer):
    """Обрабатывает модель пользователей User."""

    class Meta:
        model = mod.User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'password'
        )

    def validate_username(self, username):
        valid.username_regex_validator(username)
        # valid.uniq_username_validator(username)
        return username
