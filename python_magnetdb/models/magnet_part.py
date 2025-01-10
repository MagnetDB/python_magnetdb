from django.db import models


class MagnetPart(models.Model):
    class Meta:
        db_table = 'magnet_parts'
    id = models.BigAutoField(primary_key=True)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=False)
    part = models.ForeignKey('Part', on_delete=models.CASCADE, null=False)
    commissioned_at = models.DateTimeField(null=False)
    decommissioned_at = models.DateTimeField(null=True)
    angle = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    def active(self):
        return self.decommissioned_at is None
