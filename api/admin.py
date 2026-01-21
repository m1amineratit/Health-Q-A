from django.contrib import admin
from .models import Question, Answer

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'instagram_username', 'doctor', 'category', 'status', 'created_at', 'views_count')
    search_fields = ('instagram_username', 'doctor__username', 'category', 'question_text')
    list_filter = ('status', 'created_at', 'category')
    readonly_fields = ('id', 'created_at', 'views_count')
    fieldsets = (
        ('Question Info', {'fields': ('id', 'question_text', 'instagram_username', 'instagram_user_id')}),
        ('Assignment', {'fields': ('doctor', 'category')}),
        ('Status', {'fields': ('status', 'answer_sent')}),
        ('Metadata', {'fields': ('created_at', 'views_count')}),
    )

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answered_by', 'answer_sent', 'created_at', 'views_count')
    search_fields = ('question__question_text', 'answered_by__username')
    list_filter = ('answer_sent', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'views_count')