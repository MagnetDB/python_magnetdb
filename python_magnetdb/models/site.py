from django.db import models

# Import MSite from python_magnetgeo
from python_magnetgeo.MSite import MSite


class Site(models.Model):
    class Meta:
        db_table = "sites"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    status = models.CharField(max_length=255, null=False)
    config_attachment = models.ForeignKey("StorageAttachment", on_delete=models.SET_NULL, null=True)
    metadata = models.JSONField(default=dict, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    def to_geometry_object(self):
        """Build and return the MSite object for this site."""
        from python_magnetgeo.deserialize import unserialize_object
        import json

        magnets = []
        screens = []
        z_offset = []
        r_offset = []
        paralax = []

        for site_magnet in self.sitemagnet_set.all():
            magnet_json = site_magnet.magnet.geometry_config_to_json
            print("magnet_json:", magnet_json)
            magnets.append(unserialize_object(json.loads(magnet_json)))
            z_offset.append(site_magnet.z_offset)
            r_offset.append(site_magnet.r_offset)
            paralax.append(site_magnet.parallax)

        return MSite(
            name=self.name,
            magnets=magnets,
            screens=screens,
            z_offset=z_offset,
            r_offset=r_offset,
            paralax=paralax,
        )

    @property
    def geometry_config_to_json(self):
        return self.to_geometry_object().to_json()

    @property
    def geometry_config_to_yaml(self):
        return self.to_geometry_object().to_yaml()
