from django.urls import path
from . import views
from . import api_views
from . import views_email
from . import views_customer

app_name = 'devices'

urlpatterns = [
    # Device API endpoints
    path('heartbeat/', views.device_heartbeat, name='device_heartbeat'),
    path('capture/', api_views.capture_upload, name='capture_upload'),
    path('trigger/', api_views.manual_trigger, name='manual_trigger'),
    path('click-status/', api_views.click_status, name='click_status'),
    path('capture/<int:capture_id>/acknowledge/', views_email.acknowledge_capture_api, name='acknowledge_capture'),
    
    # Customer portal
    path('dashboard/', views_customer.dashboard, name='dashboard'),
    path('gallery/', views_customer.gallery, name='gallery'),
    path('settings/', views_customer.settings, name='settings'),
    path('billing/', views_customer.billing, name='billing'),
    
    # Email webhook endpoints
    path('email/sendgrid-inbound/', views_email.sendgrid_inbound_webhook, name='sendgrid_inbound'),
    path('email/webhook/', views_email.generic_email_webhook, name='generic_email_webhook'),
    
    # Stripe webhook
    path('stripe/webhook/', api_views.stripe_webhook, name='stripe_webhook'),
]

