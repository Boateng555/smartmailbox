from rest_framework import serializers
from .models import Device, DeviceCapture, SIM


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'id', 'serial_number', 'status', 'owner', 'last_seen', 'created_at',
            'ir_sensor_status', 'last_motion_time', 'connection_type'
        ]


class DeviceCaptureSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCapture
        fields = ['id', 'device', 'image', 'captured_at']
        read_only_fields = ['captured_at']


class HeartbeatSerializer(serializers.Serializer):
    serial_number = serializers.CharField(max_length=100)
    connection_type = serializers.ChoiceField(
        choices=[('wifi', 'WiFi'), ('cellular', 'Cellular'), ('unknown', 'Unknown')],
        default='unknown',
        required=False
    )


class CaptureRequestSerializer(serializers.Serializer):
    serial_number = serializers.CharField(max_length=100)
    image = serializers.CharField()  # Base64 encoded image
    motion_detected = serializers.BooleanField(default=False, required=False)
    connection_type = serializers.ChoiceField(
        choices=[('wifi', 'WiFi'), ('cellular', 'Cellular'), ('unknown', 'Unknown')],
        default='unknown',
        required=False
    )

