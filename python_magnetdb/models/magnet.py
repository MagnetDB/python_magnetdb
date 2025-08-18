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
                'innerbore': self.inner_bore if self.inner_bore is not None else 0,
                'outerbore': self.outer_bore if self.outer_bore is not None else 0,
            }
        }
        
        if self.type == MagnetType.INSERT:
            config['__tag__'] = 'Insert'
            config['__value__']['helices'] = []
            config['__value__']['rings'] = []
            config['__value__']['currentleads'] = []
            config['__value__']['hangles'] = []
            config['__value__']['rangles'] = []
            config['__value__']['probes'] = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.HELIX:
                    config['__value__']['helices'].append(magnet_part.part.name)
                    config['__value__']['hangles'].append(magnet_part.angle if magnet_part.angle is not None else 0)
                elif magnet_part.part.type == PartType.RING:
                    config['__value__']['rings'].append(magnet_part.part.name)
                    config['__value__']['rangles'].append(magnet_part.angle if magnet_part.angle is not None else 0)
                elif magnet_part.part.type == PartType.LEAD:
                    config['__value__']['currentleads'].append(magnet_part.part.name)
        elif self.type == MagnetType.SUPRAS:
            config['__tag__'] = 'Supras'
            config['__value__']['magnets'] = []
            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.SUPRA:
                    config['__value__']['magnets'].append(magnet_part.part.name)
                elif magnet_part.part.type == PartType.LEAD:
                    config['__value__']['currentleads'].append(magnet_part.part.name)
        elif self.type == MagnetType.BITTERS:
            config['__tag__'] = 'Bitters'
            config['__value__']['magnets'] = []
            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.BITTER:
                    config['__value__']['magnets'].append(magnet_part.part.name)
                elif magnet_part.part.type == PartType.LEAD:
                    config['__value__']['currentleads'].append(magnet_part.part.name)

        # add Probes
        for probe in self.probe_set.all():
            config['__value__']['probes'].append(probe.name)  
        return json.dumps(config)

    @property
    def geometry_config_to_yaml(self):
        json_config = self.geometry_config_to_json
        if json_config is None:
            return None
        return json_to_yaml(json_config)
