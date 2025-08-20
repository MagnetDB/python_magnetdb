import enum
from django.db import models

class CadAttachmentType(str, enum.Enum):
    AXI = 'axi'
    THREE_DIMENSIONS = '3d'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

class CadAttachment(models.Model):
    class Meta:
        db_table = 'cad_attachments'
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=255, null=False, choices=CadAttachmentType.choices(), default=CadAttachmentType.THREE_DIMENSIONS)
    attachment = models.ForeignKey('StorageAttachment', on_delete=models.CASCADE, null=False)
    part = models.ForeignKey('Part', on_delete=models.CASCADE, null=True)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('Site', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
