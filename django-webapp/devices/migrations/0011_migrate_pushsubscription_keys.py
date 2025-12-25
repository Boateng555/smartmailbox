# Generated migration to migrate PushSubscription keys field to separate p256dh and auth fields
import json
from django.db import migrations, models


def migrate_keys_to_separate_fields(apps, schema_editor):
    """Migrate keys JSON field to separate p256dh and auth fields"""
    PushSubscription = apps.get_model('devices', 'PushSubscription')
    
    for subscription in PushSubscription.objects.all():
        try:
            # Parse the old keys JSON field
            if subscription.keys:
                keys_dict = json.loads(subscription.keys)
                subscription.p256dh = keys_dict.get('p256dh', '')
                subscription.auth = keys_dict.get('auth', '')
                subscription.save()
        except (json.JSONDecodeError, AttributeError, TypeError):
            # If keys field is invalid or missing, set empty defaults
            subscription.p256dh = ''
            subscription.auth = ''
            subscription.save()


def reverse_migrate(apps, schema_editor):
    """Reverse migration: combine p256dh and auth back into keys JSON"""
    PushSubscription = apps.get_model('devices', 'PushSubscription')
    
    for subscription in PushSubscription.objects.all():
        keys_dict = {
            'p256dh': subscription.p256dh or '',
            'auth': subscription.auth or ''
        }
        subscription.keys = json.dumps(keys_dict)
        subscription.save()


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0010_notification_preferences'),
    ]

    operations = [
        # Add new fields as nullable first
        migrations.AddField(
            model_name='pushsubscription',
            name='p256dh',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='pushsubscription',
            name='auth',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        # Migrate data from keys to new fields
        migrations.RunPython(migrate_keys_to_separate_fields, reverse_migrate),
        # Make fields non-nullable after data migration
        migrations.AlterField(
            model_name='pushsubscription',
            name='p256dh',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='pushsubscription',
            name='auth',
            field=models.CharField(max_length=100),
        ),
        # Remove old keys field (if it exists)
        migrations.RemoveField(
            model_name='pushsubscription',
            name='keys',
        ),
        # Remove updated_at field if it exists
        migrations.RemoveField(
            model_name='pushsubscription',
            name='updated_at',
        ),
    ]

