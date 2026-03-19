"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet
from ..models.magnet import MagnetType

data_directory = getenv("DATA_DIR")


LTS = create_material(
    {
        "name": "LTS",
        "nuance": "LTS",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 1.0e10,
        "thermal_conductivity": 360,
        "magnet_permeability": 1,
        "young": 127e9,
        "poisson": 0.335,
        "expansion_coefficient": 18e-6,
        "rpe": 481000000.0,
    }
)

HYBRID = create_part(
    {"name": "Hybrid", "type": "supra", "geometry": "Hybrid", "status": "in_study", "material": LTS}
)

MHYBRID = create_magnet(
    {
        "name": "Hybrid",
        "type": MagnetType.SUPRAS,
        "status": "in_study",
        "parts": [HYBRID],
    }
)
