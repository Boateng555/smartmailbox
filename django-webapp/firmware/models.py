from django.db import models
from django.core.validators import FileExtensionValidator


class FirmwareVersion(models.Model):
    version = models.CharField(max_length=50, unique=True, help_text="Version number (e.g., 1.0.0)")
    file = models.FileField(
        upload_to='firmware/',
        validators=[FileExtensionValidator(allowed_extensions=['bin'])],
        help_text="Firmware binary file (.bin)"
    )
    release_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Only active versions are available for OTA updates")
    release_notes = models.TextField(blank=True, help_text="Release notes and changelog")
    file_size = models.IntegerField(help_text="File size in bytes", default=0)
    
    class Meta:
        ordering = ['-release_date']
        verbose_name = "Firmware Version"
        verbose_name_plural = "Firmware Versions"
    
    def __str__(self):
        return f"v{self.version} ({'Active' if self.is_active else 'Inactive'})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
