import copy
import enum
import json

from django.db import models

from python_magnetdb.utils.yaml_json import json_to_yaml


class PartType(str, enum.Enum):
    SUPRA = 'supra'
    HELIX = 'helix'
    RING = 'ring'
    SCREEN = 'screen'
    LEAD = 'lead'
    BITTER = 'bitter'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Part(models.Model):
    class Meta:
        db_table = 'parts'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    type = models.CharField(max_length=255, null=False, choices=PartType.choices())
    status = models.CharField(max_length=255, null=False)
    material = models.ForeignKey('Material', on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    design_office_reference = models.CharField(max_length=255, null=True)
    geometry_config = models.JSONField(default=dict, null=False)
    hts_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True, related_name='part_hts')
    shape_attachment = models.ForeignKey('StorageAttachment', on_delete=models.SET_NULL, null=True, related_name='part_shape')

    @property
    def allow_hts_file(self):
        return self.type == PartType.SUPRA

    @property
    def allow_shape_file(self):
        return self.type == PartType.HELIX

    @property
    def geometry_config_to_json(self):
        if self.geometry_config is None:
            return None

        config = copy.deepcopy(self.geometry_config)
        config['__value__']['name'] = self.name
        return json.dumps(config)

    @property
    def geometry_config_to_yaml(self):
        json_config = self.geometry_config_to_json
        if json_config is None:
            return None
        return json_to_yaml(json_config)
