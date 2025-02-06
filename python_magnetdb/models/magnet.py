import enum
import json

from django.db import models

from python_magnetdb.models.part import PartType
from python_magnetdb.utils.yaml_json import json_to_yaml


class MagnetType(str, enum.Enum):
    INSERT = 'insert'
    BITTERS = 'bitters'
    SUPRAS = 'supras'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

    @property
    def supported_part_types(self):
        if self == MagnetType.INSERT:
            return [PartType.HELIX, PartType.RING, PartType.SCREEN, PartType.LEAD]
        elif self == MagnetType.BITTERS:
            return [PartType.BITTER, PartType.SCREEN, PartType.LEAD]
        elif self == MagnetType.SUPRAS:
            return [PartType.SUPRA, PartType.SCREEN, PartType.LEAD]
        return []


class Magnet(models.Model):
    class Meta:
        db_table = 'magnets'
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=255, null=False, choices=MagnetType.choices())
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    inner_bore = models.FloatField(null=True)
    outer_bore = models.FloatField(null=True)
    status = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    design_office_reference = models.CharField(max_length=255, null=True)
    metadata = models.JSONField(default=dict, null=False)
    flow_params = models.JSONField(null=True)

    @property
    def geometry_config_to_json(self):
        config = {
            '__tag__': 'Unknown',
            '__value__': {
                'name': self.name,
                'inner_bore': self.inner_bore,
                'outer_bore': self.outer_bore,
            }
        }
        if self.type == MagnetType.INSERT:
            config['__tag__'] = 'Insert'
            config['__value__']['Helices'] = []
            config['__value__']['Rings'] = []
            config['__value__']['CurrentLeads'] = []
            config['__value__']['HAngles'] = []
            config['__value__']['RAngles'] = []
            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.HELIX:
                    config['__value__']['Helices'].append(magnet_part.part.name)
                    config['__value__']['HAngles'].append(magnet_part.angle)
                elif magnet_part.part.type == PartType.RING:
                    config['__value__']['Rings'].append(magnet_part.part.name)
                    config['__value__']['RAngles'].append(magnet_part.angle)
                elif magnet_part.part.type == PartType.LEAD:
                    config['__value__']['CurrentLeads'].append(magnet_part.part.name)
        elif self.type == MagnetType.SUPRAS:
            config['__tag__'] = 'Supras'
            config['__value__']['magnets'] = []
            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.SUPRA:
                    config['__value__']['magnets'].append(magnet_part.part.name)
                elif magnet_part.part.type == PartType.LEAD:
                    config['__value__']['CurrentLeads'].append(magnet_part.part.name)
        elif self.type == MagnetType.BITTERS:
            config['__tag__'] = 'Bitters'
            config['__value__']['magnets'] = []
            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.BITTER:
                    config['__value__']['magnets'].append(magnet_part.part.name)
                elif magnet_part.part.type == PartType.LEAD:
                    config['__value__']['CurrentLeads'].append(magnet_part.part.name)
        return json.dumps(config)

    @property
    def geometry_config_to_yaml(self):
        json_config = self.geometry_config_to_json
        if json_config is None:
            return None
        return json_to_yaml(json_config)
