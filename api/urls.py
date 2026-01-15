from django.urls import path
from . import views, json_api

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('webhook/', views.instagram_webhook, name='instagram_webhook'),
    path('answer/<uuid:question_id>/', views.answer_question, name='answer_question'),
    path('view/<uuid:question_id>/', views.public_answer, name='public_answer'),
    path("privacy-policy/", views.privacy_policy),

    # JSON API Views
    path('api/auth/login/', json_api.login_api, name='api_login'),
    path('api/auth/me/', json_api.get_current_user_api, name='api_me'),
    path("register/", json_api.register_api, name="register_api"),
    
    path('api/questions/', json_api.get_questions_api, name='api_get_questions'),
    path('api/questions/<uuid:question_id>/', json_api.get_question_detail_api, name='api_get_question_detail'),
    path('api/questions/<uuid:question_id>/answer/', json_api.submit_answer_api, name='api_submit_answer'),
]
