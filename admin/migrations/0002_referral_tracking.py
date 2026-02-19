from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferralClick',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_clicks', to='admin.adminrole')),
            ],
        ),
        migrations.CreateModel(
            name='ReferralSignup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_signups', to='admin.adminrole')),
                ('doctor', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referral_signup', to='account.doctor')),
            ],
        ),
    ]
