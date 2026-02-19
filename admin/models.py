from django.db import models
from django.contrib.auth.models import User
import uuid


class AdminRole(models.Model):
    """Admin/Viseur/Affiliate role for dashboard users"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('viseur', 'Viseur'),
        ('affiliate', 'Affiliation'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    referral_link = models.CharField(max_length=255, unique=True, blank=True)
    views_count = models.IntegerField(default=0)
    invites_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_link:
            self.referral_link = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class ReferralClick(models.Model):
    """Track affiliate referral link clicks"""
    admin_role = models.ForeignKey(AdminRole, on_delete=models.CASCADE, related_name='referral_clicks')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin_role.referral_link} - {self.created_at:%Y-%m-%d %H:%M:%S}"


class ReferralSignup(models.Model):
    """Track signups attributed to an affiliate referral link"""
    admin_role = models.ForeignKey(AdminRole, on_delete=models.CASCADE, related_name='referral_signups')
    doctor = models.OneToOneField('account.Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='referral_signup')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        doctor_name = self.doctor.user.get_full_name() if self.doctor else "Unknown doctor"
        return f"{doctor_name} -> {self.admin_role.referral_link}"


class OfferCategory(models.Model):
    """Category for offers (e.g., Hotelerie, Homme, etc.)"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Offer Categories"

    def __str__(self):
        return self.name


class Offer(models.Model):
    """Promotional offers for the platform"""
    title = models.CharField(max_length=200)
    short_description = models.TextField()
    long_description = models.TextField()
    logo = models.ImageField(upload_to='offer_logos/', blank=True, null=True)
    transaction_value = models.CharField(max_length=50)  # e.g., "10%"
    category = models.ForeignKey(OfferCategory, on_delete=models.CASCADE, related_name='offers')
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.category.name}"


class UserRequest(models.Model):
    """Pending requests for establishments (Liste des demandes)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('declined', 'Declined'),
        ('confirmed', 'Confirmed'),
    ]
    establishment_type = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    contact_rdv = models.BooleanField(default=False)
    visite = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.establishment_type} ({self.status})"
