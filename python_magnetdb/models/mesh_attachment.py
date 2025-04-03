import enum

from django.db import models


class MeshAttachmentType(str, enum.Enum):
    AXI = 'axi'
    THREE_DIMENSIONS = '3d'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class MeshAttachment(models.Model):
    class Meta:
        db_table = 'mesh_attachments'
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=255, null=False, choices=MeshAttachmentType.choices())
    attachment = models.ForeignKey('StorageAttachment', on_delete=models.CASCADE, null=False)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('Site', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
