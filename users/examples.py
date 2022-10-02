import random
import string

from drf_spectacular.utils import OpenApiExample

LOGIN_SUCCESS = OpenApiExample(
    name='Успех',
    value={'token': ''.join(
        random.choice(string.digits + string.ascii_lowercase) for _ in range(40))},
    status_codes=[200],
    response_only=True,
)

USER_NOT_FOUND = OpenApiExample(
    name='Пользователь не найден',
    value={'error': 'user not found'},
    status_codes=[400],
    response_only=True,
)

WRONG_PASSWORD = OpenApiExample(
    name='Неверный пароль',
    value={'error': 'wrong credentials'},
    status_codes=[401],
    response_only=True,
)

PASSWORD_RECOVERY_SUCCESS = OpenApiExample(
    name='Успех',
    value={'success': 'new password was sent to <email>'},
    status_codes=[200],
    response_only=True,
)

INCORRECT_ROLE_MSG = {'error': f'role must be `seller` or `buyer`'}
INCORRECT_ROLE = OpenApiExample(
    name='Неверный тип пользователя',
    value=INCORRECT_ROLE_MSG,
    status_codes=[400],
    response_only=True,
)