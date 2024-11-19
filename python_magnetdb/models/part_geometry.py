from django.db import models


class PartGeometry(models.Model):
    class Meta:
        db_table = 'part_geometries'
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=255, null=False)
    part = models.ForeignKey('Part', on_delete=models.CASCADE, null=False)
    attachment = models.ForeignKey('StorageAttachment', on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
