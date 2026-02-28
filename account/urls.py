from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .api import (
    # Auth views
    register_api,
    login_api,
    get_current_user_api,
    password_reset_request_api,
    password_reset_confirm_api,
    accept_user_api,
    set_password_api,
    track_referral_click_api,
    # Doctor views
    get_doctor_profile_api,
    get_doctor_statistics_api,
    update_doctor_api,
    # Establishment views
    create_establishment_api,
    get_establishment_profile_api,
    update_establishment_api,
    # Subscription views
    get_subscription_status_api,
)

urlpatterns = [
    # Authentication
    path('api/auth/register', register_api, name='api_register'),
    path('api/auth/login', login_api, name='api_login'),
    path('api/auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me', get_current_user_api, name='api_me'),

    # Referral Tracking
    path('api/referral/<str:code>', track_referral_click_api, name='api_referral_click'),
    
    # Password Reset
    path('api/auth/password-reset', password_reset_request_api, name='api_password_reset_request'),
    path('api/auth/password-reset-confirm', password_reset_confirm_api, name='api_password_reset_confirm'),
    
    # User Acceptance & Password Setup
    path('api/auth/accept-user', accept_user_api, name='api_accept_user'),
    path('api/auth/set-password', set_password_api, name='api_set_password'),
    
    # Doctor Profile
    path('api/doctor/profile', get_doctor_profile_api, name='api_get_doctor_profile'),
    path('api/doctor/statistics', get_doctor_statistics_api, name='api_doctor_statistics'),
    path('api/doctor/update', update_doctor_api, name='api_update_doctor'),

    # Establishment Profile
    path('api/establishment/create', create_establishment_api, name='api_create_establishment'),
    path('api/establishment/profile', get_establishment_profile_api, name='api_get_establishment_profile'),
    path('api/establishment/update', update_establishment_api, name='api_update_establishment'),

    # Subscription
    path('api/subscription/status', get_subscription_status_api, name='api_subscription_status'),
]
