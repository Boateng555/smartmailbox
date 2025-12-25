# Generated migration to remove IR sensor fields and add trigger_type
# Run: python manage.py migrate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0006_capture'),
    ]

    operations = [
        # Remove IR sensor fields from Device
        migrations.RemoveField(
            model_name='device',
            name='ir_sensor_status',
        ),
        migrations.RemoveField(
            model_name='device',
            name='last_motion_time',
        ),
        # Update Capture model: replace motion_detected with trigger_type
        migrations.RemoveField(
            model_name='capture',
            name='motion_detected',
        ),
        migrations.AddField(
            model_name='capture',
            name='trigger_type',
            field=models.CharField(
                choices=[('automatic', 'Automatic (Timer)'), ('manual', 'Manual (User Request)')],
                default='automatic',
                help_text='How this capture was triggered',
                max_length=20
            ),
        ),
    ]


