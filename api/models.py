import uuid
from django.db import models
from django.conf import settings

# Create your models here.

class Question(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('archived', 'Archived'),
    ]
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    category = models.CharField(max_length=150, blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instagram_username = models.CharField(max_length=100)
    instagram_user_id = models.CharField(max_length=100, blank=True)
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    views_count = models.IntegerField(default=0, help_text="Number of views for this question")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q from @{self.instagram_username} - {self.created_at.strftime('%Y-%m-%d')}"


class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer', help_text="One answer per question")
    answered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    answer_sent = models.BooleanField(default=False, help_text="Whether the answer has been sent to the user")
    views_count = models.IntegerField(default=0, help_text="Number of views for this answer")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Answer to: {self.question.question_text[:50]}... by {self.answered_by.username if self.answered_by else 'Unknown'}"
