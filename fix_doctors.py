#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')
django.setup()

from account.models import Doctor
from django.contrib.auth.models import User

# Check existing doctors
print(f"Total doctors: {Doctor.objects.count()}")
null_count = Doctor.objects.filter(is_accepted__isnull=True).count()
print(f"Doctors with null is_accepted: {null_count}")

# If there are null values, update them
if null_count > 0:
    Doctor.objects.filter(is_accepted__isnull=True).update(is_accepted=False)
    print(f"✅ Fixed {null_count} doctor records")

# Verify the fix
print(f"After fix - Doctors with null is_accepted: {Doctor.objects.filter(is_accepted__isnull=True).count()}")

# Test creating a new doctor
try:
    test_user = User.objects.create_user(
        username='testdoctor2',
        email='testdoctor2@example.com',
        first_name='Test',
        last_name='Doctor'
    )
    
    doctor = Doctor.objects.create(
        user=test_user,
        speciality='eyes'
    )
    print(f"✅ Test doctor created successfully: {doctor}")
except Exception as e:
    print(f"❌ Error creating test doctor: {e}")
    # Clean up if user was created
    try:
        test_user.delete()
    except:
        pass
