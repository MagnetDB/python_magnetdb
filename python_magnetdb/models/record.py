from django.db import models


class Record(models.Model):
    class Meta:
        db_table = 'records'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    site = models.ForeignKey('Site', on_delete=models.CASCADE, null=False)
    attachment = models.ForeignKey('StorageAttachment', on_delete=models.CASCADE, null=False)
    metadata = models.JSONField(default=dict, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
