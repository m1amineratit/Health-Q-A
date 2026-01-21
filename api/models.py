import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Question(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('archived', 'Archived'),
    ]
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    category = models.CharField(max_length=150, blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instagram_username = models.CharField(max_length=100)
    instagram_user_id = models.CharField(max_length=100, blank=True)
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    answered_at = models.DateTimeField(null=True, blank=True)
    answer_text = models.TextField(blank=True)
    answer_sent = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0, help_text="Number of views for this answer page")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q from @{self.instagram_username} - {self.created_at.strftime('%Y-%m-%d')}"

