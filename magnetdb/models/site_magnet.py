from django.db import models


class SiteMagnet(models.Model):
    id = models.BigAutoField(primary_key=True)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=False)
    site = models.ForeignKey('Site', on_delete=models.CASCADE, null=False)
    commissioned_at = models.DateTimeField(null=False)
    decommissioned_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    def active(self):
        return self.decommissioned_at is None

    class Meta:
        db_table = 'site_magnets'
