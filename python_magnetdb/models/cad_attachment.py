from django.db import models


class CadAttachment(models.Model):
    class Meta:
        db_table = 'cad_attachments'
    id = models.BigAutoField(primary_key=True)
    attachment = models.ForeignKey('StorageAttachment', on_delete=models.CASCADE, null=False)
    part = models.ForeignKey('Part', on_delete=models.CASCADE, null=True)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('Site', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
