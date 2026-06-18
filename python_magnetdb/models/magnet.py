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
    inner_bore = models.FloatField(null=True, help_text="Inner bore radius in mm")
    outer_bore = models.FloatField(null=True, help_text="Outer bore radius in mm")
    status = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    design_office_reference = models.CharField(max_length=255, null=True)
    metadata = models.JSONField(default=dict, null=False)
    flow_params = models.JSONField(null=True)

    def to_geometry_object(self):
        """Build and return the python_magnetgeo object for this magnet."""
        from python_magnetgeo.deserialize import unserialize_object
        import copy

        eps = 0.9  # clearance in mm for bore fallback calculations

        probes = [unserialize_object(p.geometry_config_to_json) for p in self.probe_set.all()]

        if self.type == MagnetType.INSERT:
            helices, hangles, rings, rangles, currentleads = [], [], [], [], []
            for mp in self.magnetpart_set.all():
                config = copy.deepcopy(mp.part.geometry_config)
                config["name"] = mp.part.name
                if mp.part.type == PartType.HELIX:
                    config.setdefault("__classname__", "Helix")
                    helices.append(unserialize_object(config))
                    hangles.append(mp.angle if mp.angle is not None else 0)
                elif mp.part.type == PartType.RING:
                    config.setdefault("__classname__", "Ring")
                    rings.append(unserialize_object(config))
                    rangles.append(mp.angle if mp.angle is not None else 0)
                elif mp.part.type == PartType.LEAD:
                    config.setdefault("__classname__", "InnerCurrentLead")
                    currentleads.append(unserialize_object(config))
            return Insert(
                name=self.name,
                helices=helices,
                rings=rings,
                currentleads=currentleads,
                hangles=hangles,
                rangles=rangles,
                innerbore=self.inner_bore if self.inner_bore is not None else (helices[0].r[0] - eps if helices else 0),
                outerbore=self.outer_bore if self.outer_bore is not None else (helices[-1].r[1] + eps if helices else 0),
                probes=probes,
            )

        elif self.type == MagnetType.SUPRAS:
            magnets, currentleads = [], []
            for mp in self.magnetpart_set.all():
                config = copy.deepcopy(mp.part.geometry_config)
                config["name"] = mp.part.name
                if mp.part.type == PartType.SUPRA:
                    magnets.append(unserialize_object(config))
                elif mp.part.type == PartType.LEAD:
                    currentleads.append(unserialize_object(config))
            return Supras(
                name=self.name,
                magnets=magnets,
                innerbore=self.inner_bore if self.inner_bore is not None else (magnets[0].r[0] - eps if magnets else 0),
                outerbore=self.outer_bore if self.outer_bore is not None else (magnets[-1].r[1] + eps if magnets else 0),
                probes=probes,
            )

        elif self.type == MagnetType.BITTERS:
            magnets, currentleads = [], []
            for mp in self.magnetpart_set.all():
                config = copy.deepcopy(mp.part.geometry_config)
                config["name"] = mp.part.name
                if mp.part.type == PartType.BITTER:
                    magnets.append(unserialize_object(config))
                elif mp.part.type == PartType.LEAD:
                    currentleads.append(unserialize_object(config))
            return Bitters(
                name=self.name,
                magnets=magnets,
                innerbore=self.inner_bore if self.inner_bore is not None else (magnets[0].r[0] - eps if magnets else 0),
                outerbore=self.outer_bore if self.outer_bore is not None else (magnets[-1].r[1] + eps if magnets else 0),
                probes=probes,
            )

        return None

    def _fallback_geo_dict(self):
        return {
            "name": self.name,
            "innerbore": self.inner_bore if self.inner_bore is not None else 0,
            "outerbore": self.outer_bore if self.outer_bore is not None else 0,
        }

    @property
    def geometry_config_to_json(self):
        geo = self.to_geometry_object()
        if geo is not None:
            return geo.to_json()
        return json.dumps({"__tag__": "Unknown", "__value__": self._fallback_geo_dict()})

    @property
    def geometry_config_to_yaml(self):
        import yaml
        print(
            f"Generating geometry_config_to_yaml for magnet {self.name} of type {self.type} ...",
            flush=True,
        )
        geo = self.to_geometry_object()
        if geo is not None:
            return geo.to_yaml()
        return yaml.dump(self._fallback_geo_dict(), default_flow_style=False)
