import copy
import enum
import json

from django.db import models


class PartType(str, enum.Enum):
    SUPRA = "supra"
    HELIX = "helix"
    RING = "ring"
    SCREEN = "screen"
    LEAD = "lead"
    BITTER = "bitter"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Part(models.Model):
    class Meta:
        db_table = "parts"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    type = models.CharField(max_length=255, null=False, choices=PartType.choices())
    status = models.CharField(max_length=255, null=False)
    material = models.ForeignKey("Material", on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    design_office_reference = models.CharField(max_length=255, null=True)
    geometry_config = models.JSONField(default=dict, null=False)
    hts_attachment = models.ForeignKey(
        "StorageAttachment", on_delete=models.SET_NULL, null=True, related_name="part_hts"
    )
    modelaxi_attachment = models.ForeignKey(
        "StorageAttachment", on_delete=models.SET_NULL, null=True, related_name="part_modelaxi"
    )
    shape_attachment = models.ForeignKey(
        "StorageAttachment", on_delete=models.SET_NULL, null=True, related_name="part_shape"
    )
    metadata = models.JSONField(default=dict, null=False)

    @property
    def allow_hts_file(self):
        return self.type == PartType.SUPRA

    @property
    def allow_shape_file(self):
        return self.type == PartType.HELIX

    @property
    def allow_modelaxi_file(self):
        return self.type == PartType.HELIX or self.type == PartType.BITTER

    def to_geometry_object(self):
        """Build and return the python_magnetgeo object for this part, or None if geometry_config is empty."""
        if self.geometry_config is None or self.geometry_config == {}:
            return None
        from python_magnetgeo.deserialize import unserialize_object
        config = copy.deepcopy(self.geometry_config)
        config["name"] = self.name
        return unserialize_object(config)

    @property
    def geometry_config_to_json(self):
        obj = self.to_geometry_object()
        if obj is None:
            return None
        result = obj.to_json()
        print(f"geometry_config_to_json[{obj.name}]:", result)
        return result

    @property
    def geometry_config_to_yaml(self):
        obj = self.to_geometry_object()
        if obj is None:
            return None
        result = obj.to_yaml()
        print(f"geometry_config_to_yaml[{obj.name}]:", self.geometry_config)
        print("object:\n", obj)
        print("yaml:\n", result)
        return result
