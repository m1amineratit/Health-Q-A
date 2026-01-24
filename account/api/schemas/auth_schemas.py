# Authentication Swagger Schemas
from drf_yasg import openapi


register_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'speciality': openapi.Schema(type=openapi.TYPE_STRING, description='Medical speciality'),
        'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
    },
    required=['speciality', 'full_name', 'email', 'phone_number']
)

login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    },
    required=['username', 'password']
)

password_reset_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
    },
    required=['email']
)

password_reset_confirm_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID (base64 encoded)'),
        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Reset token'),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
    },
    required=['uid', 'token', 'new_password']
)

accept_user_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'action': openapi.Schema(type=openapi.TYPE_STRING, description='accept or reject'),
    },
    required=['user_id', 'action']
)

set_password_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
        'password_confirm': openapi.Schema(type=openapi.TYPE_STRING, description='Password confirmation'),
    },
    required=['password', 'password_confirm']
)
