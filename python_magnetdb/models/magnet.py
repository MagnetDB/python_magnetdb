from django.db import models


class Magnet(models.Model):
    class Meta:
        db_table = 'magnets'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    status = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    design_office_reference = models.CharField(max_length=255, null=True)
    geometry_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True)

    def get_type(self):
        for magnetpart in self.magnetpart_set:
            if magnetpart.part.type == 'helix':
                return 'helix'
            elif magnetpart.part.type == 'bitter':
                return 'bitter'
            elif magnetpart.part.type == 'supra':
                return 'supra'
