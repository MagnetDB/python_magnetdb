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
        Convert probe configuration to JSON-serializable dictionary.

        Returns a dictionary representation of the probe configuration
        that can be used with python_magnetgeo's unserialize_object.

        Returns:
            dict: Dictionary representation of the Probe configuration
        """
        # Return config dictionary with Probe structure
        return {
            "__classname__": "Probe",
            "name": self.name,
            "type": self.type,
            "labels": self.labels,
            "points": self.points,
        }

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

        config = copy.deepcopy(self.geometry_config)
        config["name"] = self.name

        # Deserialize to get a magnetgeo object
        obj = unserialize_object(config)

        # Use object's to_yaml() method for proper YAML serialization
        print(f"geometry_config_to_yaml[{obj.name}]:", config)
        print("object:\n", obj)
        print("yaml:\n", obj.to_yaml())
        return obj.to_yaml()
