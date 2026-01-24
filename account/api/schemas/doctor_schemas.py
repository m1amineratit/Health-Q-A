# Doctor Swagger Schemas
from drf_yasg import openapi


doctor_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password (optional)'),
        'speciality': openapi.Schema(type=openapi.TYPE_STRING, description='Medical speciality'),
        'number_of_phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
        'instagram_account': openapi.Schema(type=openapi.TYPE_STRING, description='Instagram account handle'),
        'inpe': openapi.Schema(type=openapi.TYPE_STRING, description='INPE number'),
        'ville': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
    }
)
