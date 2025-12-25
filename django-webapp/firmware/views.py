from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import Http404
from .models import FirmwareVersion
from .serializers import FirmwareVersionSerializer


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow ESP32 devices to check for updates
def latest_firmware(request):
    """
    Returns the latest active firmware version information.
    """
    try:
        latest = FirmwareVersion.objects.filter(is_active=True).order_by('-release_date').first()
        
        if not latest:
            return Response({
                'error': 'No active firmware version available'
            }, status=404)
        
        serializer = FirmwareVersionSerializer(latest, context={'request': request})
        return Response(serializer.data)
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=500)
