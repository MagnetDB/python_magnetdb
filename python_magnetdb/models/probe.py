import json
import enum

from django.db import models

from python_magnetdb.utils.yaml_json import json_to_yaml
from django.contrib.postgres.fields import ArrayField

class ProbeType(str, enum.Enum):
    VOLTAGE = "voltage_taps"
    TEMPERATURE = "temperature"
    BFIELD = "magnetic_field"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

class Probe(models.Model):
    class Meta:
        db_table = 'probes'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    type =  models.CharField(max_length=255, null=False, choices=ProbeType.choices())
    description = models.TextField(null=True)
    # add foreignkey for magnet
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=False)
    part = models.ForeignKey('Part', on_delete=models.CASCADE, null=True)
    index = ArrayField(
        models.CharField(max_length=100),
        size=None,  # No limit on array size
        default=list,
        blank=True,
        help_text="List of probes string ids"
    )
    
    # Passer en json??
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
                'index': self.index,
                'location': self.locations,
            }
        }

        return json.dumps(config)

    @property
    def geometry_config_to_yaml(self):
        json_config = self.geometry_config_to_json
        if json_config is None:
            return None
        return json_to_yaml(json_config)
