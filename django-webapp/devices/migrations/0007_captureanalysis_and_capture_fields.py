# Generated migration for CaptureAnalysis model and Capture field updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0006_capture'),
    ]

    operations = [
        # Add new fields to Capture model
        migrations.AddField(
            model_name='capture',
            name='door_open',
            field=models.BooleanField(default=False, help_text='Door state when capture was taken'),
        ),
        migrations.AddField(
            model_name='capture',
            name='battery_voltage',
            field=models.FloatField(blank=True, help_text='Battery voltage at capture time', null=True),
        ),
        migrations.AddField(
            model_name='capture',
            name='solar_charging',
            field=models.BooleanField(default=False, help_text='Solar charging status at capture time'),
        ),
        
        # Create CaptureAnalysis model
        migrations.CreateModel(
            name='CaptureAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary', models.CharField(help_text="AI-generated summary (e.g., 'Large Amazon package detected')", max_length=500)),
                ('detected_objects', models.JSONField(default=list, help_text='List of detected objects with labels and confidence')),
                ('package_detected', models.BooleanField(default=False)),
                ('letter_detected', models.BooleanField(default=False)),
                ('envelope_detected', models.BooleanField(default=False)),
                ('detected_text', models.TextField(blank=True, help_text='All detected text from OCR')),
                ('return_addresses', models.JSONField(default=list, help_text='Extracted return addresses')),
                ('logos_detected', models.JSONField(default=list, help_text='Detected company logos/brands')),
                ('estimated_size', models.CharField(blank=True, help_text="Estimated size (e.g., 'Large', 'Medium', 'Small')", max_length=50)),
                ('bounding_boxes', models.JSONField(default=list, help_text='Bounding boxes for detected objects')),
                ('analysis_timestamp', models.DateTimeField(auto_now_add=True)),
                ('confidence_score', models.FloatField(blank=True, help_text='Overall confidence score', null=True)),
                ('processing_time_ms', models.IntegerField(blank=True, help_text='Time taken to process (ms)', null=True)),
                ('email_sent', models.BooleanField(default=False)),
                ('email_sent_at', models.DateTimeField(blank=True, null=True)),
                ('capture', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='devices.capture')),
            ],
            options={
                'ordering': ['-analysis_timestamp'],
                'verbose_name_plural': 'Capture Analyses',
            },
        ),
    ]







