import json

from django.db import models

from python_magnetdb.utils.yaml_json import json_to_yaml


class Part(models.Model):
    class Meta:
        db_table = 'parts'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    type = models.CharField(max_length=255, null=False)
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
        return self.type == 'supra'

    @property
    def allow_shape_file(self):
        return self.type == 'helix'

    @property
    def geometry_config_to_yaml(self):
        if self.geometry_config is None:
            return None
        return json_to_yaml(json.dumps(self.geometry_config))

    @property
    def geometry_config_to_json(self):
        if self.geometry_config is None:
            return None
        return json.dumps(self.geometry_config)
