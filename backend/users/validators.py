from django.core.validators import RegexValidator

import users.constants as const


def username_regex_validator(username):
    username_validator = RegexValidator(
        regex=const.USERNAME_REGEX,
        message=const.USERNAME_REGEX_TEXT
    )
    username_validator(username)
    return username
