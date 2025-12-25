# Notification Flow - User App Integration

## Overview

This document describes the complete notification flow from ESP32 capture → ChatGPT analysis → User notification, including subscription and click limit handling in the mobile app.

## Complete Notification Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32-CAM Device                         │
│  • Wakes every 2 hours (automatic)                          │
│  • Or wakes on manual trigger (if queued)                   │
│  • Captures photo                                            │
│  • Uploads to server                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ POST /api/device/capture/
                        │ {
                        │   "serial_number": "ESP-12345",
                        │   "image": "base64...",
                        │   "trigger_type": "automatic"|"manual"
                        │ }
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloud Server (Django)                       │
│  1. Save capture to database                                 │
│  2. Queue for ChatGPT analysis                               │
│  3. Return capture_id immediately                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Async processing
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              ChatGPT Vision API                              │
│  • Analyze image                                             │
│  • Detect mail presence                                      │
│  • Return: {mail_detected, confidence, description}         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Analysis result
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Notification Service                            │
│  • Check user preferences                                    │
│  • Send push notification                                    │
│  • Send email (optional)                                     │
│  • Send SMS (optional)                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Push notification
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Mobile App (User Device)                        │
│  • Receive push notification                                  │
│  • Display notification                                       │
│  • Update UI with result                                     │
│  • Show "Mail detected" or "Mailbox empty"                   │
└─────────────────────────────────────────────────────────────┘
```

## Mobile App Integration

### 1. Manual Trigger Button

```javascript
// React Native / React example

import React, { useState, useEffect } from 'react';
import { Button, Alert, Text, View } from 'react-native';

function MailboxCheckButton({ deviceSerial, userId }) {
  const [loading, setLoading] = useState(false);
  const [clicksUsed, setClicksUsed] = useState(0);
  const [clicksLimit, setClicksLimit] = useState(3);
  const [canClick, setCanClick] = useState(true);
  const [userTier, setUserTier] = useState('free');
  
  // Load click status on mount
  useEffect(() => {
    loadClickStatus();
  }, []);
  
  const loadClickStatus = async () => {
    try {
      const response = await fetch(`/api/device/status/?serial=${deviceSerial}`);
      const data = await response.json();
      
      setClicksUsed(data.clicks_used_today);
      setClicksLimit(data.clicks_limit);
      setCanClick(data.clicks_used_today < data.clicks_limit || data.user_tier === 'premium');
      setUserTier(data.user_tier);
    } catch (error) {
      console.error('Failed to load click status:', error);
    }
  };
  
  const handleManualTrigger = async () => {
    // Check if user can click
    if (!canClick && userTier === 'free') {
      Alert.alert(
        'Daily Limit Reached',
        `You have used all ${clicksLimit} manual clicks for today. Upgrade to Premium for unlimited clicks!`,
        [
          { text: 'OK' },
          { text: 'Upgrade', onPress: () => navigateToSubscription() }
        ]
      );
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/device/trigger/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          device_serial: deviceSerial,
          user_id: userId
        })
      });
      
      const data = await response.json();
      
      if (response.status === 200 || response.status === 202) {
        // Success - trigger queued
        Alert.alert(
          'Trigger Sent',
          data.message || 'Device will capture photo on next wake cycle',
          [{ text: 'OK' }]
        );
        
        // Update click count
        setClicksUsed(prev => prev + 1);
        if (userTier === 'free' && clicksUsed + 1 >= clicksLimit) {
          setCanClick(false);
        }
      } else if (response.status === 429) {
        // Click limit exceeded
        Alert.alert(
          'Daily Limit Reached',
          data.message,
          [
            { text: 'OK' },
            { text: 'Upgrade', onPress: () => navigateToSubscription() }
          ]
        );
        setCanClick(false);
      } else {
        // Error
        Alert.alert('Error', data.error || 'Failed to trigger device');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error. Please try again.');
      console.error('Trigger error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <View>
      <Button
        title={loading ? 'Triggering...' : 'Check Mailbox'}
        onPress={handleManualTrigger}
        disabled={loading || (!canClick && userTier === 'free')}
      />
      
      {userTier === 'free' && (
        <Text style={{ marginTop: 10, textAlign: 'center' }}>
          {clicksUsed} / {clicksLimit} clicks used today
        </Text>
      )}
      
      {!canClick && userTier === 'free' && (
        <Text style={{ marginTop: 5, color: 'red', textAlign: 'center' }}>
          Limit reached. Resets at midnight.
        </Text>
      )}
    </View>
  );
}
```

### 2. Push Notification Handler

```javascript
// Handle incoming push notifications

import { Notifications } from 'expo-notifications';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Listen for notifications
useEffect(() => {
  const subscription = Notifications.addNotificationReceivedListener(notification => {
    const data = notification.request.content.data;
    
    if (data.mail_detected) {
      // Mail detected
      showMailDetectedNotification(data);
    } else {
      // Mailbox empty
      showMailboxEmptyNotification(data);
    }
  });
  
  return () => subscription.remove();
}, []);

function showMailDetectedNotification(data) {
  Alert.alert(
    '📬 Mail Detected',
    data.description || 'New mail in your mailbox!',
    [
      { text: 'View', onPress: () => navigateToCapture(data.capture_id) },
      { text: 'OK' }
    ]
  );
}

function showMailboxEmptyNotification(data) {
  // Optional: Only show if user has this preference enabled
  if (userPreferences.notifyOnEmpty) {
    Alert.alert(
      '📭 Mailbox Empty',
      'Your mailbox is empty',
      [{ text: 'OK' }]
    );
  }
}
```

### 3. Click Limit Display Component

```javascript
function ClickLimitDisplay({ deviceSerial }) {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    loadStatus();
    // Refresh every minute
    const interval = setInterval(loadStatus, 60000);
    return () => clearInterval(interval);
  }, []);
  
  const loadStatus = async () => {
    try {
      const response = await fetch(`/api/device/status/?serial=${deviceSerial}`);
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load status:', error);
    }
  };
  
  if (!status) return null;
  
  const { user_tier, clicks_used_today, clicks_limit, clicks_reset_at } = status;
  
  if (user_tier === 'premium') {
    return (
      <View style={styles.premiumBadge}>
        <Text>⭐ Premium - Unlimited Clicks</Text>
      </View>
    );
  }
  
  const clicksRemaining = clicks_limit - clicks_used_today;
  const resetTime = new Date(clicks_reset_at);
  const now = new Date();
  const hoursUntilReset = Math.ceil((resetTime - now) / (1000 * 60 * 60));
  
  return (
    <View style={styles.clickLimitContainer}>
      <Text style={styles.clickLimitText}>
        {clicks_used_today} / {clicks_limit} clicks used today
      </Text>
      {clicksRemaining > 0 ? (
        <Text style={styles.clicksRemaining}>
          {clicksRemaining} remaining
        </Text>
      ) : (
        <Text style={styles.limitReached}>
          Limit reached. Resets in {hoursUntilReset} hours
        </Text>
      )}
    </View>
  );
}
```

### 4. Subscription Upgrade Flow

```javascript
function SubscriptionUpgrade({ userTier, onUpgrade }) {
  if (userTier === 'premium') {
    return null; // Already premium
  }
  
  return (
    <View style={styles.upgradeContainer}>
      <Text style={styles.upgradeTitle}>Upgrade to Premium</Text>
      <Text style={styles.upgradeDescription}>
        Get unlimited manual clicks and priority support
      </Text>
      <Button
        title="Upgrade Now"
        onPress={handleUpgrade}
      />
    </View>
  );
  
  const handleUpgrade = async () => {
    try {
      // Redirect to subscription page or Stripe checkout
      const response = await fetch('/api/subscription/create-checkout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          tier: 'premium'
        })
      });
      
      const data = await response.json();
      
      if (data.checkout_url) {
        // Open Stripe checkout
        Linking.openURL(data.checkout_url);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to start upgrade process');
    }
  };
}
```

## Notification Types

### 1. Mail Detected Notification

**Push Notification:**
```
Title: 📬 Mail Detected
Body: [ChatGPT description] or "New mail in your mailbox"
Data: {
  capture_id: 123,
  analysis_id: 456,
  mail_detected: true,
  confidence: 0.92,
  description: "2 envelopes visible"
}
```

**App Display:**
- Show notification banner
- Update mailbox status to "Mail Present"
- Display capture image
- Show ChatGPT analysis details

### 2. Mailbox Empty Notification

**Push Notification:**
```
Title: 📭 Mailbox Empty
Body: Your mailbox is empty
Data: {
  capture_id: 123,
  analysis_id: 456,
  mail_detected: false,
  confidence: 0.95
}
```

**App Display:**
- Optional notification (user preference)
- Update mailbox status to "Empty"
- Display capture image
- Show "No mail detected" message

## Click Limit Logic

### Free Users

1. **Initial State**: 0 clicks used, 3 clicks limit
2. **On Click**: Increment count, check if limit reached
3. **Limit Reached**: Disable button, show upgrade prompt
4. **Reset**: At midnight (user's timezone), reset to 0

### Premium Users

1. **Unlimited Clicks**: No limit checking
2. **Button Always Enabled**: Can click anytime
3. **No Count Display**: Don't show click counter

## User Preferences

```javascript
const defaultPreferences = {
  notifyOnMail: true,        // Notify when mail detected
  notifyOnEmpty: false,      // Notify when mailbox empty
  notifyViaPush: true,       // Push notifications
  notifyViaEmail: true,       // Email notifications
  notifyViaSMS: false,        // SMS notifications
  quietHoursStart: 22,        // 10 PM
  quietHoursEnd: 7,           // 7 AM
};
```

## Error Handling

### Network Errors
- Retry with exponential backoff
- Show user-friendly error messages
- Queue requests when offline

### API Errors
- Handle 429 (rate limit) gracefully
- Show click limit messages
- Handle 402 (payment required) for subscriptions

### Device Offline
- Queue trigger request
- Show "Device offline" message
- Retry when device comes online

## Testing Checklist

- [ ] Manual trigger button works
- [ ] Click limit enforced for free users
- [ ] Premium users have unlimited clicks
- [ ] Click count resets at midnight
- [ ] Push notifications received
- [ ] Notifications display correctly
- [ ] Upgrade flow works
- [ ] Error handling works
- [ ] Offline queueing works


