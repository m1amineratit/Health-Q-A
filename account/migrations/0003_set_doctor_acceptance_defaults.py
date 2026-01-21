# Data migration to set default values for is_accepted field

from django.db import migrations


def set_default_is_accepted(apps, schema_editor):
    """Set is_accepted=False for any doctor records with null values"""
    Doctor = apps.get_model('account', 'Doctor')
    Doctor.objects.filter(is_accepted__isnull=True).update(is_accepted=False)


def reverse_set_default(apps, schema_editor):
    """Reverse function - no-op since we're just setting defaults"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_doctor_acceptance_fields'),
    ]

    operations = [
        migrations.RunPython(set_default_is_accepted, reverse_set_default),
    ]
