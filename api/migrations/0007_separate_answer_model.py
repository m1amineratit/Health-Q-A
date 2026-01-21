# Generated migration for separating Answer model from Question

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0006_question_views_count_alter_question_answered_by_and_more'),
    ]

    operations = [
        # Create Answer model
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('answer_sent', models.BooleanField(default=False, help_text='Whether the answer has been sent to the user')),
                ('views_count', models.IntegerField(default=0, help_text='Number of views for this answer')),
                ('answered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='answers', to=settings.AUTH_USER_MODEL)),
                ('question', models.OneToOneField(help_text='One answer per question', on_delete=django.db.models.deletion.CASCADE, related_name='answer', to='api.question')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        # Remove old answer-related fields from Question
        migrations.RemoveField(
            model_name='question',
            name='answered_by',
        ),
        migrations.RemoveField(
            model_name='question',
            name='answered_at',
        ),
        migrations.RemoveField(
            model_name='question',
            name='answer_text',
        ),
        migrations.RemoveField(
            model_name='question',
            name='answer_sent',
        ),
    ]
