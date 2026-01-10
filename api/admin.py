from django.contrib import admin
from .models import Question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['instagram_username', 'created_at', 'status', 'answered_by', 'answer_sent']
    list_filter = ['status', 'answered_by', 'created_at']
    search_fields = ['instagram_username', 'question_text', 'answer_text']
    readonly_fields = ['id', 'created_at']
