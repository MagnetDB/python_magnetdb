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

    @property
    def geometry_config_to_json(self):
        """
        Convert geometry_config to JSON string.

        Creates a python_magnetgeo object from geometry_config, updates the name,
        and returns the JSON representation using the object's to_json() method.

        Returns:
            str: JSON string or None if geometry_config is empty
        """
        if self.geometry_config is None or self.geometry_config == {}:
            return None

        # Create python_magnetgeo object from geometry_config
        from python_magnetgeo.deserialize import unserialize_object

        config = copy.deepcopy(self.geometry_config)
        config["name"] = self.name

        # Deserialize to get a magnetgeo object
        obj = unserialize_object(config)

        # Use object's native to_json() method
        print(f"geometry_config_to_json[{obj.name}]:", obj.to_json())
        return obj.to_json()

    @property
    def geometry_config_to_yaml(self):
        """
        Convert geometry_config to YAML string.

        Creates a python_magnetgeo object from geometry_config, updates the name,
        and returns the YAML representation using yaml.dump().

        Returns:
            str: YAML string or None if geometry_config is empty
        """
        if self.geometry_config is None or self.geometry_config == {}:
            return None

        # Create python_magnetgeo object from geometry_config
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        config = copy.deepcopy(self.geometry_config)
        config["name"] = self.name

        # Deserialize to get a magnetgeo object
        obj = unserialize_object(config)

        # Use object's to_yaml() method for proper YAML serialization
        print(f"geometry_config_to_yaml[{obj.name}]:", config)
        print("object:\n", obj)
        print("yaml:\n", obj.to_yaml())
        return obj.to_yaml()
