from django.urls import path
from . import json_api

urlpatterns = [
    # Questions
    path('api/questions/', json_api.get_questions_api, name='api_get_questions'),
    path('api/questions/<uuid:question_id>/', json_api.get_question_detail_api, name='api_get_question_detail'),
    path('api/questions/<uuid:question_id>/answer/', json_api.submit_answer_api, name='api_submit_answer'),
    path('api/feed/answered-questions/', json_api.answered_questions_feed_api, name='api_answered_questions_feed'),
    path('api/feed/answered-questions/', json_api.answered_questions_feed_api, name='api_unanswered_questions_feed'),
]

