from pydoc import classname

from django.db import models


class AuditLog(models.Model):
    class Meta:
        db_table = 'audit_logs'
    id = models.BigAutoField(primary_key=True)
    message = models.TextField(null=False)
    metadata = models.JSONField(null=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=False)
    resource_type = models.TextField(null=False)
    resource_id = models.BigIntegerField(null=True)
    resource_name = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    @classmethod
    def log(cls, user, message, metadata=None, resource=None, resource_name=None):
        log = cls(message=message, metadata=metadata, user=user)
        if resource is not None:
            log.resource_type = resource.__class__.__name__
            if hasattr(resource, 'name'):
                log.resource_name = resource.name
        if resource_name is not None:
            log.resource_name = resource_name
        log.save()
        return log
