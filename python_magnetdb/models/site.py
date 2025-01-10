import json

from django.db import models

from python_magnetdb.utils.yaml_json import json_to_yaml


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

    @property
    def geometry_config_to_json(self):
        config = {
            '__tag__': 'MSite',
            '__value__': {
                'name': self.name,
                'magnets': [],
                'z_offset': [],
                'r_offset': [],
                'paralax': [],
            }
        }
        for site_magnet in self.sitemagnet_set.all():
            config['__value__']['magnets'].append(site_magnet.magnet.name)
            config['__value__']['z_offset'].append(site_magnet.z_offset)
            config['__value__']['r_offset'].append(site_magnet.r_offset)
            config['__value__']['paralax'].append(site_magnet.parallax)
        return json.dumps(config)

    @property
    def geometry_config_to_yaml(self):
        json_config = self.geometry_config_to_json
        if json_config is None:
            return None
        return json_to_yaml(json_config)
