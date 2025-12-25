# Production Upgrade Roadmap - Smart Mailbox System

Complete roadmap for production-ready smart mailbox system with cellular-first connectivity, subscriptions, and business logic.

## ✅ Phase 1: Core Infrastructure (COMPLETED)

### Subscription & Billing System ✅
- [x] Subscription models (Plan, CustomerSubscription, DataUsage, PaymentHistory)
- [x] Stripe integration service
- [x] Billing logic and usage checks
- [x] Management commands for billing automation
- [x] Stripe webhook handler

### Device Lifecycle Management ✅
- [x] Device lifecycle states (pre_activation, active_subscription, suspended, returned, decommissioned)
- [x] Device state machine methods
- [x] Subscription validation before operations
- [x] Device activation flow

### A7670 Cellular Driver ✅
- [x] A7670 header file (`a7670_cellular.h`)
- [x] A7670 implementation (`a7670_cellular.cpp`)
- [x] Power control, network registration, PPP connection
- [x] HTTP client over cellular

### API Integration ✅
- [x] Subscription checks in capture upload
- [x] Usage limit validation
- [x] Data usage tracking
- [x] 402 Payment Required responses
- [x] 429 Too Many Requests responses

## 🚧 Phase 2: ESP32 Firmware (IN PROGRESS)

### Cellular-First Connectivity
- [x] A7670 driver created
- [x] Cellular-first priority logic
- [ ] Complete integration in main.cpp
- [ ] WiFi fallback (signal > -70dBm)
- [ ] SD card backup system
- [ ] Retry logic for failed uploads

### Power Management
- [ ] Deep sleep optimization (30 min intervals)
- [ ] Battery percentage reporting
- [ ] Low battery alerts (<20%)
- [ ] Power state tracking

### Photo Capture
- [ ] 3 photos sequence (immediate, +1s, +2s)
- [ ] JPEG compression (80% quality)
- [ ] Total size <500KB per sequence
- [ ] Batch upload in single request

## 📋 Phase 3: Customer Portal (PENDING)

### Dashboard (`/dashboard/`)
- [x] View created
- [ ] Template implementation
- [ ] Real-time device status
- [ ] Battery percentage display
- [ ] Data usage meter
- [ ] Recent mail activity

### Gallery (`/gallery/`)
- [x] View created
- [ ] Template implementation
- [ ] AI-categorized photos
- [ ] Search and filter
- [ ] Download functionality

### Settings (`/settings/`)
- [x] View created
- [ ] Template implementation
- [ ] Subscription management
- [ ] Notification preferences
- [ ] Device management

### Billing (`/billing/`)
- [x] View created
- [ ] Template implementation
- [ ] Payment method management
- [ ] Invoice history
- [ ] Usage analytics
- [ ] Plan upgrade/downgrade

## 📋 Phase 4: Admin Dashboard (PENDING)

### Customer Management
- [ ] Customer list view
- [ ] Subscription status monitoring
- [ ] Payment issue resolution
- [ ] Support ticket system

### Device Management
- [x] Device admin enhanced
- [ ] Device inventory tracking
- [ ] Firmware update deployment
- [ ] Connection status monitoring
- [ ] Battery level alerts

### Business Analytics
- [ ] Monthly Recurring Revenue (MRR)
- [ ] Customer acquisition metrics
- [ ] Churn rate tracking
- [ ] Device activation rates
- [ ] Support ticket resolution

## 📋 Phase 5: Business Logic (PENDING)

### Customer Onboarding
- [ ] Device claiming flow
- [ ] 7-day free trial creation
- [ ] Payment method collection
- [ ] Trial to paid conversion

### Billing Automation
- [x] Management command created
- [ ] Celery task for daily billing
- [ ] Failed payment retry logic
- [ ] Grace period handling
- [ ] Automatic suspension

### Data Usage
- [x] Usage tracking implemented
- [ ] Monthly reset automation
- [ ] Overage warnings (80%, 95%)
- [ ] Automatic upgrade suggestions

## 📋 Phase 6: SD Card Backup (PENDING)

### Hardware Setup
- [ ] MicroSD module on SPI
- [ ] CS pin: GPIO 15
- [ ] Library integration (SD.h or similar)

### Software Logic
- [ ] Save failed uploads to SD
- [ ] Filename: capture_YYYYMMDD_HHMMSS.jpg
- [ ] Metadata JSON with each capture
- [ ] Retry upload on next wake
- [ ] Delete after successful upload

## 📋 Phase 7: Deployment (READY)

### Server Setup
- [x] Hetzner CPX11 setup script
- [x] SSL certificate automation
- [x] Monitoring setup
- [x] Backup scripts

### Configuration
- [ ] Environment variables setup
- [ ] Stripe keys configuration
- [ ] Domain DNS configuration
- [ ] SSL certificate installation

## 🔧 Configuration Required

### Stripe Setup
1. Create Stripe account
2. Get API keys (test and live)
3. Create products for each plan tier
4. Configure webhook endpoint: `https://yourdomain.com/api/device/stripe/webhook/`
5. Set webhook secret

### Environment Variables
```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Subscription Plans (auto-created)
# Run: python manage.py create_subscription_plans
```

### ESP32 Configuration
```cpp
// A7670 pins
#define A7670_POWER_PIN      4
#define A7670_RX_PIN         16
#define A7670_TX_PIN         17

// APN (carrier-specific)
#define CELLULAR_APN         "internet"
```

## 📊 Database Migrations

Run migrations:
```bash
python manage.py migrate
python manage.py create_subscription_plans
```

## 🚀 Quick Start

1. **Setup Subscriptions**
   ```bash
   python manage.py create_subscription_plans
   ```

2. **Configure Stripe**
   - Add Stripe keys to `.env.production`
   - Configure webhook in Stripe dashboard

3. **Deploy to Hetzner**
   ```bash
   sudo bash deployment/hetzner/setup.sh yourcamera.com
   ```

4. **Setup Billing Automation**
   ```bash
   # Add to crontab
   0 0 * * * python manage.py process_billing
   0 1 * * * python manage.py check_suspended_devices
   ```

## 📈 Next Priorities

1. **Complete ESP32 Firmware** - SD card backup, photo compression
2. **Customer Portal Templates** - Dashboard, gallery, settings, billing
3. **Admin Dashboard** - Business analytics and management
4. **Testing** - End-to-end flow testing
5. **Documentation** - User guides and API docs

## 📝 Notes

- All subscription models are created and migrated
- Stripe integration is ready (needs configuration)
- Device lifecycle management is implemented
- A7670 driver is created (needs integration testing)
- Customer portal views are created (need templates)
- Admin dashboard is enhanced (need analytics views)

The foundation is solid. Remaining work is primarily:
- Template creation for customer portal
- ESP32 firmware completion
- Admin analytics dashboard
- End-to-end testing







