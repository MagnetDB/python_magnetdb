import enum
import json

from django.db import models

from python_magnetdb.models.part import PartType

# Import python_magnetgeo classes
from python_magnetgeo.Insert import Insert
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras


class MagnetType(str, enum.Enum):
    INSERT = "insert"
    BITTERS = "bitters"
    SUPRAS = "supras"

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
        db_table = "magnets"

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
        """
        Convert magnet to python_magnetgeo object and serialize to JSON.

        Uses python_magnetgeo classes (Insert, Supras, Bitters) to create
        geometry objects with proper validation, then serializes using their
        built-in to_json() method.

        Returns:
            str: JSON string representation with __classname__ format
        """
        from python_magnetgeo.deserialize import unserialize_object
        import copy

        # Collect probe names
        probes = []
        for probe in self.probe_set.all():
            config = probe.geometry_config_to_json
            # Deserialize to get a magnetgeo object
            probe_obj = unserialize_object(config)
            probes.append(probe_obj)

        if self.type == MagnetType.INSERT:
            # Collect helices, rings, and current leads as objects
            helices = []
            hangles = []
            rings = []
            rangles = []
            currentleads = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.HELIX:
                    # Deserialize geometry_config to get Helix object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Ensure __classname__ is set for proper deserialization
                    if "__classname__" not in config:
                        config["__classname__"] = "Helix"
                    helix_obj = unserialize_object(config)
                    helices.append(helix_obj)
                    hangles.append(magnet_part.angle if magnet_part.angle is not None else 0)
                elif magnet_part.part.type == PartType.RING:
                    # Deserialize geometry_config to get Ring object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Ensure __classname__ is set for proper deserialization
                    if "__classname__" not in config:
                        config["__classname__"] = "Ring"
                    ring_obj = unserialize_object(config)
                    rings.append(ring_obj)
                    rangles.append(magnet_part.angle if magnet_part.angle is not None else 0)
                elif magnet_part.part.type == PartType.LEAD:
                    # Deserialize geometry_config to get CurrentLead object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Ensure __classname__ is set for proper deserialization
                    if "__classname__" not in config:
                        config["__classname__"] = "InnerCurrentLead"
                    lead_obj = unserialize_object(config)
                    currentleads.append(lead_obj)

            # Create Insert object with validation
            insert = Insert(
                name=self.name,
                helices=helices,
                rings=rings,
                currentleads=currentleads,
                hangles=hangles,
                rangles=rangles,
                innerbore=self.inner_bore if self.inner_bore is not None else 0,
                outerbore=self.outer_bore if self.outer_bore is not None else 0,
                probes=probes,
            )
            return insert.to_json()

        elif self.type == MagnetType.SUPRAS:
            # Collect supra magnets and current leads as objects
            magnets = []
            currentleads = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.SUPRA:
                    # Deserialize geometry_config to get Supra object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    supra_obj = unserialize_object(config)
                    magnets.append(supra_obj)
                elif magnet_part.part.type == PartType.LEAD:
                    # Deserialize geometry_config to get CurrentLead object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    lead_obj = unserialize_object(config)
                    currentleads.append(lead_obj)

            # Create Supras object with validation
            supras = Supras(
                name=self.name,
                magnets=magnets,
                innerbore=self.inner_bore if self.inner_bore is not None else 0,
                outerbore=self.outer_bore if self.outer_bore is not None else 0,
                probes=probes,
            )
            return supras.to_json()

        elif self.type == MagnetType.BITTERS:
            # Collect bitter magnets and current leads as objects
            magnets = []
            currentleads = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.BITTER:
                    # Deserialize geometry_config to get Bitter object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    bitter_obj = unserialize_object(config)
                    magnets.append(bitter_obj)
                elif magnet_part.part.type == PartType.LEAD:
                    # Deserialize geometry_config to get CurrentLead object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    lead_obj = unserialize_object(config)
                    currentleads.append(lead_obj)

            # Create Bitters object with validation
            bitters = Bitters(
                name=self.name,
                magnets=magnets,
                innerbore=self.inner_bore if self.inner_bore is not None else 0,
                outerbore=self.outer_bore if self.outer_bore is not None else 0,
                probes=probes,
            )
            return bitters.to_json()

        # Fallback for unknown types
        return json.dumps(
            {
                "__tag__": "Unknown",
                "__value__": {
                    "name": self.name,
                    "innerbore": self.inner_bore if self.inner_bore is not None else 0,
                    "outerbore": self.outer_bore if self.outer_bore is not None else 0,
                },
            }
        )

    @property
    def geometry_config_to_yaml(self):
        """
        Convert magnet to python_magnetgeo object and serialize to YAML.

        Uses python_magnetgeo classes (Insert, Supras, Bitters) to create
        geometry objects with proper validation, then serializes using yaml.dump().

        Returns:
            str: YAML string representation with proper YAML tags
        """
        from python_magnetgeo.deserialize import unserialize_object
        import copy
        import yaml

        print(
            f"Generating geometry_config_to_yaml for magnet {self.name} of type {self.type} ...",
            flush=True,
        )
        # Collect probe names
        probes = []
        for probe in self.probe_set.all():
            config = probe.geometry_config_to_json
            # Deserialize to get a magnetgeo object
            probe_obj = unserialize_object(config)
            probes.append(probe_obj)

        if self.type == MagnetType.INSERT:
            print(
                f"Processing INSERT magnet {self.name} with {len(self.magnetpart_set.all())} parts ...",
                flush=True,
            )
            # Collect helices, rings, and current leads as objects
            helices = []
            hangles = []
            rings = []
            rangles = []
            currentleads = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.HELIX:
                    # Deserialize geometry_config to get Helix object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object
                    helix_obj = unserialize_object(config)
                    helices.append(helix_obj)
                    hangles.append(magnet_part.angle if magnet_part.angle is not None else 0)
                elif magnet_part.part.type == PartType.RING:
                    # Deserialize geometry_config to get Ring object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object
                    ring_obj = unserialize_object(config)
                    rings.append(ring_obj)
                    rangles.append(magnet_part.angle if magnet_part.angle is not None else 0)
                elif magnet_part.part.type == PartType.LEAD:
                    # Deserialize geometry_config to get CurrentLead object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object
                    lead_obj = unserialize_object(config)
                    currentleads.append(lead_obj)

            # Create Insert object with validation
            eps = 0.5
            insert = Insert(
                name=self.name,
                helices=helices,
                rings=rings,
                currentleads=currentleads,
                hangles=hangles,
                rangles=rangles,
                innerbore=(
                    self.inner_bore
                    if self.inner_bore is not None or self.inner_bore == 0
                    else helices[0].r[0] - eps
                ),
                outerbore=(
                    self.outer_bore
                    if self.outer_bore is not None or self.outer_bore == 0
                    else helices[-1].r[1] + eps
                ),
                probes=probes,
            )
            return insert.to_yaml()

        elif self.type == MagnetType.SUPRAS:
            print(
                f"Processing SUPRAS magnet {self.name} with {len(self.magnetpart_set.all())} parts ...",
                flush=True,
            )
            # Collect supra magnets and current leads as objects
            magnets = []
            currentleads = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.SUPRA:
                    # Deserialize geometry_config to get Supra object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object
                    supra_obj = unserialize_object(config)
                    magnets.append(supra_obj)
                elif magnet_part.part.type == PartType.LEAD:
                    # Deserialize geometry_config to get CurrentLead object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object
                    lead_obj = unserialize_object(config)
                    currentleads.append(lead_obj)

            # Create Supras object with validation
            # Handle empty magnets list (e.g., fresh database with no parts)
            if not magnets:
                innerbore_val = self.inner_bore if self.inner_bore is not None else 0
                outerbore_val = self.outer_bore if self.outer_bore is not None else 0
            else:
                innerbore_val = (
                    self.inner_bore if self.inner_bore is not None else magnets[0].r[0] - eps
                )
                outerbore_val = (
                    self.outer_bore if self.outer_bore is not None else magnets[-1].r[1] + eps
                )

            supras = Supras(
                name=self.name,
                magnets=magnets,
                innerbore=innerbore_val,
                outerbore=outerbore_val,
                probes=probes,
            )
            return supras.to_yaml()

        elif self.type == MagnetType.BITTERS:
            print(
                f"Processing BITTERS magnet {self.name} with {len(self.magnetpart_set.all())} parts ...",
                flush=True,
            )
            # Collect bitter magnets and current leads as objects
            magnets = []
            currentleads = []

            for magnet_part in self.magnetpart_set.all():
                if magnet_part.part.type == PartType.BITTER:
                    # Deserialize geometry_config to get Bitter object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object
                    bitter_obj = unserialize_object(config)
                    magnets.append(bitter_obj)
                elif magnet_part.part.type == PartType.LEAD:
                    # Deserialize geometry_config to get CurrentLead object
                    config = copy.deepcopy(magnet_part.part.geometry_config)
                    config["name"] = magnet_part.part.name
                    # Deserialize to get a magnetgeo object

                    lead_obj = unserialize_object(config)
                    currentleads.append(lead_obj)

            # Create Bitters object with validation
            # Handle empty magnets list (e.g., fresh database with no parts)
            if not magnets:
                innerbore_val = self.inner_bore if self.inner_bore is not None else 0
                outerbore_val = self.outer_bore if self.outer_bore is not None else 0
            else:
                innerbore_val = (
                    self.inner_bore if self.inner_bore is not None else magnets[0].r[0] - eps
                )
                outerbore_val = (
                    self.outer_bore if self.outer_bore is not None else magnets[-1].r[1] + eps
                )

            bitters = Bitters(
                name=self.name,
                magnets=magnets,
                innerbore=innerbore_val,
                outerbore=outerbore_val,
                probes=probes,
            )
            return bitters.to_yaml()

        # Fallback for unknown types - return simple YAML
        fallback_data = {
            "name": self.name,
            "innerbore": self.inner_bore if self.inner_bore is not None else 0,
            "outerbore": self.outer_bore if self.outer_bore is not None else 0,
        }
        return yaml.dump(fallback_data, default_flow_style=False)
