# Generated migration for adding acceptance tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='is_accepted',
            field=models.BooleanField(default=False, help_text='Whether the doctor has been accepted by admin'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='doctor',
            name='accepted_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when doctor was accepted', null=True),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='img',
            field=models.ImageField(blank=True, null=True, upload_to='doctors_images/'),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='number_of_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='instagram_account',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='inpe',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='ville',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
