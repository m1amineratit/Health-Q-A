# Swagger Schemas Package
from .auth_schemas import (
    register_schema,
    login_schema,
    password_reset_schema,
    password_reset_confirm_schema,
    accept_user_schema,
    set_password_schema,
)
from .doctor_schemas import doctor_update_schema
from .establishment_schemas import (
    establishment_create_schema,
    establishment_update_schema,
)

__all__ = [
    # Auth schemas
    'register_schema',
    'login_schema',
    'password_reset_schema',
    'password_reset_confirm_schema',
    'accept_user_schema',
    'set_password_schema',
    # Doctor schemas
    'doctor_update_schema',
    # Establishment schemas
    'establishment_create_schema',
    'establishment_update_schema',
]
