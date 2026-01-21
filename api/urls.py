from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views, json_api

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('webhook/', views.instagram_webhook, name='instagram_webhook'),
    path('answer/<uuid:question_id>/', views.answer_question, name='answer_question'),
    path('view/<uuid:question_id>/', views.public_answer, name='public_answer'),
    path("privacy-policy/", views.privacy_policy),

    # JSON API Views
    path('api/auth/login', json_api.login_api, name='api_login'),
    path('api/auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me', json_api.get_current_user_api, name='api_me'),
    path("register", json_api.register_api, name="register_api"),
    
    # Password Reset
    path('api/auth/password-reset/', json_api.password_reset_request_api, name='api_password_reset_request'),
    path('api/auth/password-reset-confirm/', json_api.password_reset_confirm_api, name='api_password_reset_confirm'),
    
    # Doctor Profile
    path('api/doctor/profile/', json_api.get_doctor_profile_api, name='api_get_doctor_profile'),
    path('api/doctor/statistics/', json_api.get_doctor_statistics_api, name='api_doctor_statistics'),
    path('api/doctor/update/', json_api.update_doctor_api, name='api_update_doctor'),
    
    # Establishment Profile
    path('api/establishment/create/', json_api.create_establishment_api, name='api_create_establishment'),
    path('api/establishment/profile/', json_api.get_establishment_profile_api, name='api_get_establishment_profile'),
    path('api/establishment/update/', json_api.update_establishment_api, name='api_update_establishment'),
    
    path('api/questions/', json_api.get_questions_api, name='api_get_questions'),
    path('api/questions/<uuid:question_id>/', json_api.get_question_detail_api, name='api_get_question_detail'),
    path('api/questions/<uuid:question_id>/answer/', json_api.submit_answer_api, name='api_submit_answer'),
    path('api/feed/answered-questions/', json_api.answered_questions_feed_api, name='api_answered_questions_feed'),
]
