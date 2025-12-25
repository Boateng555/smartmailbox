from django.urls import path
from . import views
from . import admin_views

app_name = 'web'

urlpatterns = [
    # Auth
    path('login/', views.MobileLoginView.as_view(), name='login'),
    path('logout/', views.mobile_logout, name='logout'),
    
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('device/<str:serial>/', views.device_detail, name='device_detail'),
    path('capture/<int:capture_id>/download/', views.download_capture, name='download_capture'),
    path('gallery/', views.photo_gallery, name='photo_gallery'),
    path('gallery/<str:serial>/', views.photo_gallery, name='photo_gallery_device'),
    path('settings/', views.settings, name='settings'),
    path('claim-device/', views.claim_device, name='claim_device'),
    path('manifest.json', views.manifest, name='manifest'),
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('subscribe-push/', views.subscribe_push, name='subscribe_push'),
    path('debug/', views.debug_page, name='debug'),
    path('debug/test-websocket/<str:serial>/', views.test_websocket, name='test_websocket'),
    
    # Admin views
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/support/', admin_views.support_panel, name='support_panel'),
    path('admin/diagnostics/<str:serial>/', admin_views.device_diagnostics, name='device_diagnostics'),
    path('admin/bulk-update/', admin_views.bulk_firmware_update, name='bulk_firmware_update'),
    path('admin/api/diagnostics/<str:serial>/', admin_views.api_device_diagnostics, name='api_device_diagnostics'),
]

