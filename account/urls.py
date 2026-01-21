from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import json_api

urlpatterns = [
    # Authentication
    path('api/auth/register', json_api.register_api, name='api_register'),
    path('api/auth/login', json_api.login_api, name='api_login'),
    path('api/auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me', json_api.get_current_user_api, name='api_me'),
    
    # Password Reset
    path('api/auth/password-reset', json_api.password_reset_request_api, name='api_password_reset_request'),
    path('api/auth/password-reset-confirm', json_api.password_reset_confirm_api, name='api_password_reset_confirm'),
    
    # Doctor Profile
    path('api/doctor/profile', json_api.get_doctor_profile_api, name='api_get_doctor_profile'),
    path('api/doctor/statistics', json_api.get_doctor_statistics_api, name='api_doctor_statistics'),
    path('api/doctor/update', json_api.update_doctor_api, name='api_update_doctor'),
    
    # Establishment Profile
    path('api/establishment/create', json_api.create_establishment_api, name='api_create_establishment'),
    path('api/establishment/profile', json_api.get_establishment_profile_api, name='api_get_establishment_profile'),
    path('api/establishment/update', json_api.update_establishment_api, name='api_update_establishment'),
]
