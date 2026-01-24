# Establishment Swagger Schemas
from drf_yasg import openapi


establishment_create_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'establishment_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of establishment (cabinet, clinic, hospital, laboratory)'),
        'establishment_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of establishment'),
        'localization': openapi.Schema(type=openapi.TYPE_STRING, description='Google Maps URL'),
        'ville': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
        'commune': openapi.Schema(type=openapi.TYPE_STRING, description='Commune'),
        'quartier': openapi.Schema(type=openapi.TYPE_STRING, description='Quarter/District'),
        'adresse_electronique': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'telephone_fixe': openapi.Schema(type=openapi.TYPE_STRING, description='Fixed phone number'),
    },
    required=['establishment_type', 'establishment_name', 'adresse_electronique', 'telephone_fixe', 'ville']
)

establishment_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'establishment_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of establishment'),
        'establishment_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of establishment'),
        'localization': openapi.Schema(type=openapi.TYPE_STRING, description='Google Maps URL'),
        'ville': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
        'commune': openapi.Schema(type=openapi.TYPE_STRING, description='Commune'),
        'quartier': openapi.Schema(type=openapi.TYPE_STRING, description='Quarter/District'),
        'adresse_electronique': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'telephone_fixe': openapi.Schema(type=openapi.TYPE_STRING, description='Fixed phone number'),
    }
)
