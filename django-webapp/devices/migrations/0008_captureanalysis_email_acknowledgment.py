# Generated migration for email acknowledgment fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0007_captureanalysis_and_capture_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='captureanalysis',
            name='email_acknowledged',
            field=models.BooleanField(default=False, help_text='Customer replied to email'),
        ),
        migrations.AddField(
            model_name='captureanalysis',
            name='email_acknowledged_at',
            field=models.DateTimeField(blank=True, help_text='Customer replied to email', null=True),
        ),
    ]







