from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_alter_doctor_img'),
    ]

    operations = [
        migrations.AlterField(
            model_name='establishment',
            name='photo',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='establishment_photos'),
        ),
    ]
