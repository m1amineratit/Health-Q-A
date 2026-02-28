# API Package
from .views import (
    # Auth views
    register_api,
    login_api,
    password_reset_request_api,
    password_reset_confirm_api,
    get_current_user_api,
    accept_user_api,
    set_password_api,
    track_referral_click_api,
    # Doctor views
    get_doctor_profile_api,
    get_doctor_statistics_api,
    update_doctor_api,
    # Establishment views
    get_establishment_profile_api,
    create_establishment_api,
    update_establishment_api,
    # Subscription views
    get_subscription_status_api,
)

__all__ = [
    # Auth views
    'register_api',
    'login_api',
    'password_reset_request_api',
    'password_reset_confirm_api',
    'get_current_user_api',
    'accept_user_api',
    'set_password_api',
    'track_referral_click_api',
    # Doctor views
    'get_doctor_profile_api',
    'get_doctor_statistics_api',
    'update_doctor_api',
    # Establishment views
    'get_establishment_profile_api',
    'create_establishment_api',
    'update_establishment_api',
    # Subscription views
    'get_subscription_status_api',
]
