import enum

from django.db import models
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
        db_table = "probes"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    type = models.CharField(max_length=255, null=False, choices=ProbeType.choices())
    description = models.TextField(null=True)
    # add foreignkey for magnet
    magnet = models.ForeignKey("Magnet", on_delete=models.CASCADE, null=False)
    part = models.ForeignKey("Part", on_delete=models.CASCADE, null=True)
    labels = ArrayField(
        models.CharField(max_length=100),
        size=None,  # No limit on array size
        default=list,
        blank=True,
        help_text="List of probes string ids",
    )

    # Passer en json??
    points = ArrayField(
        ArrayField(
            models.FloatField(),
            size=3,  # Each coordinate has exactly 3 values
        ),
        size=None,  # No limit on number of coordinates
        default=list,
        blank=True,
        help_text="List of 3D coordinates as [x, y, z]",
    )
    metadata = models.JSONField(default=dict, null=False)

    @property
    def geometry_config_to_json(self):
        """
        Convert probe configuration to JSON string.

        Creates a python_magnetgeo Probe object from the probe data,
        and returns the JSON representation using the object's to_json() method.

        Returns:
            str: JSON string representation of the Probe
        """
        from python_magnetgeo.deserialize import unserialize_object

        # Build config dictionary with Probe structure
        config = {
            "__classname__": "Probe",
            "name": self.name,
            "type": self.type,
            "labels": self.labels,
            "points": self.points,
        }

        # Create Probe object and use its to_json() method
        obj = unserialize_object(config)
        return obj.to_json()

    @property
    def geometry_config_to_yaml(self):
        """
        Convert probe configuration to YAML string.

        Creates a python_magnetgeo Probe object from the probe data,
        and returns the YAML representation using yaml.dump().

        Returns:
            str: YAML string representation of the Probe
        """
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        # Build config dictionary with Probe structure
        config = {
            "__classname__": "Probe",
            "name": self.name,
            "type": self.type,
            "labels": self.labels,
            "points": self.points,
        }

        # Create Probe object and use yaml.dump()
        obj = unserialize_object(config)
        return yaml.dump(obj, sort_keys=False)
