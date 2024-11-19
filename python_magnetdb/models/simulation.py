from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from jsonfield import JSONField


class Simulation(models.Model):
    class Meta:
        db_table = 'simulations'
    id = models.BigAutoField(primary_key=True)
    status = models.TextField(default='pending', null=True)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=True)
    site = models.ForeignKey('Site', on_delete=models.CASCADE, null=True)
    method = models.TextField(null=True)
    model = models.TextField(null=True)
    geometry = models.TextField(null=True)
    cooling = models.TextField(null=True)
    output_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True, related_name='simulation_output_attachment')
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    static = models.BooleanField(null=True)
    non_linear = models.BooleanField(null=True)
    setup_output_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True, related_name='simulation_setup_output_attachment')
    setup_status = models.TextField(default='pending', null=False)
    setup_state = JSONField(default=dict)
    owner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    log_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True, related_name='simulation_log_attachment')

    @property
    def resource_type(self) -> str | None:
        if self.magnet_id is not None:
            return 'magnets'
        elif self.site_id is not None:
            return 'sites'
        return None

    @property
    def resource_id(self):
        if self.magnet_id is not None:
            return self.magnet_id
        elif self.site_id is not None:
            return self.site_id
        return None

    @property
    def resource(self):
        if self.magnet_id is not None:
            return self.magnet
        elif self.site_id is not None:
            return self.site
        return None


@receiver(pre_delete, sender=Simulation)
def delete_attachments(sender, instance, **kwargs):
    from python_magnetdb.models import StorageAttachment

    attachment_fields = [
        'setup_output_attachment',
        'output_attachment',
        'log_attachment'
    ]

    for field in attachment_fields:
        attachment_id = getattr(instance, f'{field}_id', None)
        if attachment_id:
            attachment = StorageAttachment.objects.filter(id=attachment_id).first()
            if attachment:
                attachment.delete()
