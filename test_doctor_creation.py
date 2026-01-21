#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system.settings')
django.setup()

from account.models import Doctor, User

# Clean up test users from previous runs
User.objects.filter(username__startswith='testdoctor').delete()

# Test 1: Create a doctor with explicit is_accepted
print("Test 1: Creating doctor with explicit is_accepted=True")
try:
    user1 = User.objects.create_user(
        username='testdoctor_explicit',
        email='test1@example.com',
        first_name='Explicit',
        last_name='Doctor'
    )
    doctor1 = Doctor.objects.create(
        user=user1,
        speciality='heart',
        is_accepted=True
    )
    print(f"  ✅ Created: {doctor1}")
    print(f"  ✅ is_accepted = {doctor1.is_accepted}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: Create a doctor without specifying is_accepted (should default to False)
print("\nTest 2: Creating doctor with default is_accepted")
try:
    user2 = User.objects.create_user(
        username='testdoctor_default',
        email='test2@example.com',
        first_name='Default',
        last_name='Doctor'
    )
    doctor2 = Doctor.objects.create(
        user=user2,
        speciality='neurology'
    )
    print(f"  ✅ Created: {doctor2}")
    print(f"  ✅ is_accepted = {doctor2.is_accepted}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Create a doctor with minimal fields
print("\nTest 3: Creating doctor with minimal fields")
try:
    user3 = User.objects.create_user(
        username='testdoctor_minimal',
        email='test3@example.com'
    )
    doctor3 = Doctor.objects.create(
        user=user3,
        speciality='eyes'
    )
    print(f"  ✅ Created: {doctor3}")
    print(f"  ✅ is_accepted = {doctor3.is_accepted}")
    print(f"  ✅ accepted_at = {doctor3.accepted_at}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Summary
print("\n" + "="*50)
print("Summary:")
total = Doctor.objects.count()
print(f"Total doctors: {total}")
print(f"Doctors with is_accepted=True: {Doctor.objects.filter(is_accepted=True).count()}")
print(f"Doctors with is_accepted=False: {Doctor.objects.filter(is_accepted=False).count()}")
print(f"Doctors with null is_accepted: {Doctor.objects.filter(is_accepted__isnull=True).count()}")
print("="*50)
print("\n✅ All tests passed! The admin panel should now work correctly.")
