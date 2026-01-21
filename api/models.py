import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    img = models.ImageField(upload_to='doctors_images/')
    speciality = models.CharField(
        choices=[
            ('eyes', 'Ophthalmologist'),
            ('heart', 'Cardiologist'),
            ('generaliste', 'General Practitioner'),
            ('dentist', 'Dentist'),
            ('pediatrics', 'Pediatrician'),
            ('neurology', 'Neurologist'),
        ],
        max_length=100
    )
    number_of_phone = models.CharField(max_length=20)
    instagram_account = models.CharField(max_length=100)
    inpe = models.CharField(max_length=10)
    ville = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_speciality_display()}"
    

class Establishment(models.Model):
    ESTABLISHMENT_TYPE_CHOICES = [
        ('cabinet', 'Cabinet'),
        ('clinic', 'Clinic'),
        ('hospital', 'Hospital'),
        ('laboratory', 'Laboratory'),
    ]
    
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='doctor_establishment')
    establishment_type = models.CharField(
        max_length=50,
        choices=ESTABLISHMENT_TYPE_CHOICES,
        default='cabinet'
    )
    establishment_name = models.CharField(max_length=200)
    localization = models.URLField(blank=True, null=True)
    ville = models.CharField(max_length=100)
    commune = models.CharField(max_length=100, blank=True, null=True)
    quartier = models.CharField(max_length=100, blank=True, null=True)
    adresse_electronique = models.EmailField()
    telephone_fixe = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='establishment_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.establishment_name} - {self.get_establishment_type_display()}"

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
