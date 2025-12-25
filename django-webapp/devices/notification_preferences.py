"""
Customer notification preferences and quiet hours management.
"""
import logging
from datetime import time, datetime
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationPreferences:
    """Manage customer notification preferences"""
    
    def __init__(self, user):
        self.user = user
        self.preferences = self._load_preferences()
    
    def _load_preferences(self):
        """Load preferences from user profile or defaults"""
        try:
            # Try to get from user profile if it exists
            if hasattr(self.user, 'profile'):
                return {
                    'email_enabled': getattr(self.user.profile, 'email_notifications', True),
                    'sms_enabled': getattr(self.user.profile, 'sms_notifications', False),
                    'push_enabled': getattr(self.user.profile, 'push_notifications', True),
                    'immediate': getattr(self.user.profile, 'immediate_notifications', True),
                    'quiet_hours_start': getattr(self.user.profile, 'quiet_hours_start', time(22, 0)),  # 10 PM
                    'quiet_hours_end': getattr(self.user.profile, 'quiet_hours_end', time(7, 0)),  # 7 AM
                    'quiet_hours_enabled': getattr(self.user.profile, 'quiet_hours_enabled', True),
                    'thumbnail_size': getattr(self.user.profile, 'email_thumbnail_size', 100),  # KB
                }
        except Exception as e:
            logger.debug(f"Could not load preferences from profile: {e}")
        
        # Default preferences
        return {
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'immediate': True,
            'quiet_hours_start': time(22, 0),  # 10 PM
            'quiet_hours_end': time(7, 0),  # 7 AM
            'quiet_hours_enabled': True,
            'thumbnail_size': 100,  # KB
        }
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.preferences.get('quiet_hours_enabled', True):
            return False
        
        now = timezone.now().time()
        start = self.preferences.get('quiet_hours_start', time(22, 0))
        end = self.preferences.get('quiet_hours_end', time(7, 0))
        
        # Handle quiet hours that span midnight
        if start > end:
            # Quiet hours span midnight (e.g., 10 PM to 7 AM)
            return now >= start or now <= end
        else:
            # Quiet hours within same day
            return start <= now <= end
    
    def should_send_immediate(self):
        """Check if immediate notifications are enabled"""
        return self.preferences.get('immediate', True)
    
    def should_send_email(self):
        """Check if email notifications are enabled"""
        return self.preferences.get('email_enabled', True)
    
    def should_send_sms(self):
        """Check if SMS notifications are enabled"""
        return self.preferences.get('sms_enabled', False)
    
    def should_send_push(self):
        """Check if push notifications are enabled"""
        return self.preferences.get('push_enabled', True)
    
    def get_thumbnail_size(self):
        """Get thumbnail size in KB"""
        return self.preferences.get('thumbnail_size', 100)


def get_notification_preferences(user):
    """Get notification preferences for a user"""
    return NotificationPreferences(user)


def should_send_notification(user, notification_type='email'):
    """
    Check if notification should be sent based on preferences and quiet hours.
    
    Args:
        user: User instance
        notification_type: 'email', 'sms', or 'push'
    
    Returns:
        bool: True if notification should be sent
    """
    prefs = get_notification_preferences(user)
    
    # Check if notification type is enabled
    if notification_type == 'email' and not prefs.should_send_email():
        return False
    elif notification_type == 'sms' and not prefs.should_send_sms():
        return False
    elif notification_type == 'push' and not prefs.should_send_push():
        return False
    
    # Check quiet hours (only for email and SMS, not push)
    if notification_type in ['email', 'sms']:
        if prefs.is_quiet_hours():
            logger.info(f"Quiet hours active for {user.username}, skipping {notification_type} notification")
            return False
    
    return True







