from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from .models import Doctor, Subscription

# Subscription 

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['plan', 'is_active', 'end_date']
        read_only = ['is_active', 'end_date']

# Registration Serializer - Used when creating a new account (without password)
class RegisterSerializer(serializers.Serializer):
    speciality = serializers.ChoiceField(
        choices=[
            ('eyes', 'Ophthalmologist'),
            ('heart', 'Cardiologist'),
            ('generaliste', 'General Practitioner'),
            ('dentist', 'Dentist'),
            ('pediatrics', 'Pediatrician'),
            ('neurology', 'Neurologist'),
        ]
    )
    phone_number = serializers.CharField(
        required=True
    )
    full_name = serializers.CharField(
        required=True
    )
    def validate_phone_number(self, value):
        if Doctor.objects.filter(number_of_phone=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value


# Set Password Serializer - Used when accepted user sets their password
class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password confirmation must match password"
    )
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data


# Accept User Serializer - Used by admin to accept a user
class AcceptUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    action = serializers.ChoiceField(
        choices=['accept', 'reject'],
        help_text="Choose 'accept' to approve the user or 'reject' to decline"
    )

