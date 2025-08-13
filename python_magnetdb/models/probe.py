import json

from django.db import models

from python_magnetdb.utils.yaml_json import json_to_yaml
from django.contrib.postgres.fields import ArrayField

class Probe(models.Model):
    class Meta:
        db_table = 'probes'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    type =  models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    index = ArrayField(
        models.CharField(max_length=100),
        size=None,  # No limit on array size
        default=list,
        blank=True,
        help_text="List of probes string ids"
    )
    
    locations = ArrayField(
        ArrayField(
            models.FloatField(),
            size=3,  # Each coordinate has exactly 3 values
        ),
        size=None,  # No limit on number of coordinates
        default=list,
        blank=True,
        help_text="List of 3D coordinates as [x, y, z]"
    )
    metadata = models.JSONField(default=dict, null=False)
        
    @property
    def geometry_config_to_json(self):
        config = {
            '__tag__': 'Probe',
            '__value__': {
                'name': self.name,
                'probe_type': self.type,
                'index': [],
                'location': [],
            }
        }

        return json.dumps(config)

    @property
    def geometry_config_to_yaml(self):
        json_config = self.geometry_config_to_json
        if json_config is None:
            return None
        return json_to_yaml(json_config)
