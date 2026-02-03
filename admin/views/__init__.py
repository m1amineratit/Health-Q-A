"""
Admin views package
Imports all view functions for centralized access
"""
from .auth_views import admin_login_view
from .user_views import (
    users_statistics,
    users_list,
    create_user,
    user_details,
    confirm_user,
    users_crm,
)
from .establishment_views import (
    establishments_statistics,
    establishments_list,
    establishment_practitioners,
)
from .request_views import (
    requests_list,
    update_request_status,
    decline_request,
)
from .role_views import (
    roles_statistics,
    roles_list,
    create_role,
)
from .question_views import (
    questions_statistics,
    questions_list,
    create_question,
)
from .offer_views import (
    offers_statistics,
    offers_list,
    categories_list,
    create_category,
    create_offer,
)

__all__ = [
    # Auth
    'admin_login_view',
    
    # Users
    'users_statistics',
    'users_list',
    'create_user',
    'user_details',
    'confirm_user',
    'users_crm',
    
    # Establishments
    'establishments_statistics',
    'establishments_list',
    'establishment_practitioners',

    # Requests
    'requests_list',
    'update_request_status',
    'decline_request',

    # Roles
    'roles_statistics',
    'roles_list',
    'create_role',

    # Q&A
    'questions_statistics',
    'questions_list',
    'create_question',

    # Offers
    'offers_statistics',
    'offers_list',
    'categories_list',
    'create_category',
    'create_offer',
]
