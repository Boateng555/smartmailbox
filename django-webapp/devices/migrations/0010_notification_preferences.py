# Generated migration for notification preferences
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0009_alter_captureanalysis_email_acknowledged_at'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_enabled', models.BooleanField(default=True, help_text='Enable email notifications')),
                ('sms_enabled', models.BooleanField(default=False, help_text='Enable SMS notifications')),
                ('push_enabled', models.BooleanField(default=True, help_text='Enable push notifications')),
                ('immediate', models.BooleanField(default=True, help_text='Send immediate notifications (vs hourly summaries)')),
                ('quiet_hours_start', models.TimeField(default='22:00:00', help_text='Start of quiet hours (no email/SMS)')),
                ('quiet_hours_end', models.TimeField(default='07:00:00', help_text='End of quiet hours')),
                ('quiet_hours_enabled', models.BooleanField(default=True, help_text='Enable quiet hours')),
                ('email_thumbnail_size', models.IntegerField(default=100, help_text='Email thumbnail size in KB')),
                ('phone_number', models.CharField(blank=True, help_text='Phone number for SMS (E.164 format: +1234567890)', max_length=20, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to='auth.user')),
            ],
            options={
                'verbose_name': 'Notification Preferences',
                'verbose_name_plural': 'Notification Preferences',
            },
        ),
    ]







