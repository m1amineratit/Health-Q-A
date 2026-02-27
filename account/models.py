from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    img = models.ImageField(upload_to='doctor_images/', blank=True, null=True)
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
    number_of_phone = models.CharField(max_length=20, blank=True, null=True)
    instagram_account = models.CharField(max_length=100, blank=True, null=True)
    inpe = models.CharField(max_length=10, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    is_accepted = models.BooleanField(default=False, help_text="Whether the doctor has been accepted by admin")
    accepted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when doctor was accepted")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Dr. {self.user.email} - {self.get_speciality_display()}"
    

class Subscription(models.Model):
    PLAN_CHOICES = (
        ("free", "Free"),
        ("pro", "Pro")
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    
class Establishment(models.Model): 
    ESTABLISHMENT_TYPE_CHOICES = [
        ('cabinet', 'Cabinet'),
        ('clinic', 'Clinic'),
        ('hospital', 'Hospital'),
        ('laboratory', 'Laboratory'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_establishment')
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
    photo = CloudinaryField('establishment_photos', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.establishment_name} - {self.get_establishment_type_display()}"
