from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import FirmwareVersion
from devices.models import Device


@admin.register(FirmwareVersion)
class FirmwareVersionAdmin(admin.ModelAdmin):
    list_display = ('version', 'file_size_display', 'release_date', 'is_active', 'download_link')
    list_filter = ('is_active', 'release_date')
    search_fields = ('version', 'release_notes')
    readonly_fields = ('file_size', 'release_date')
    fieldsets = (
        ('Version Information', {
            'fields': ('version', 'is_active', 'release_date')
        }),
        ('Firmware File', {
            'fields': ('file', 'file_size')
        }),
        ('Release Notes', {
            'fields': ('release_notes',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb < 1024:
                return f"{size_kb:.1f} KB"
            else:
                return f"{size_kb / 1024:.1f} MB"
        return "N/A"
    file_size_display.short_description = "File Size"
    
    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "No file"
    download_link.short_description = "Download"
    
    actions = ['push_update_to_devices']
    
    @admin.action(description='Push update to selected devices')
    def push_update_to_devices(self, request, queryset):
        """
        Admin action to notify selected devices about firmware updates.
        This sends a WebSocket message to devices to check for updates.
        """
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one firmware version.", level='error')
            return
        
        firmware = queryset.first()
        
        if not firmware.is_active:
            self.message_user(request, "Only active firmware versions can be pushed.", level='error')
            return
        
        # Get all online devices
        devices = Device.objects.filter(status='online')
        count = 0
        
        try:
            channel_layer = get_channel_layer()
            
            for device in devices:
                group_name = f'device_{device.serial_number}'
                
                # Send update notification via WebSocket
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'firmware_update',
                        'version': firmware.version,
                        'download_url': request.build_absolute_uri(firmware.file.url),
                        'file_size': firmware.file_size,
                    }
                )
                count += 1
            
            self.message_user(
                request,
                f"Firmware update notification sent to {count} device(s).",
                level='success'
            )
        except Exception as e:
            self.message_user(request, f"Error sending update: {str(e)}", level='error')
