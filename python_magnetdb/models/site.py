from django.db import models


class Site(models.Model):
    class Meta:
        db_table = 'sites'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    status = models.CharField(max_length=255, null=False)
    config_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
