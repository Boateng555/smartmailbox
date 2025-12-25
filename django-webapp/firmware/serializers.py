from rest_framework import serializers
from .models import FirmwareVersion


class FirmwareVersionSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FirmwareVersion
        fields = ['id', 'version', 'download_url', 'file_size', 'release_date', 'release_notes', 'is_active']
    
    def get_download_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None







