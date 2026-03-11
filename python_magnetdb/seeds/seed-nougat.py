"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_magnet, query_site
from python_magnetdb.models.magnet import MagnetType

data_directory = getenv("DATA_DIR")

MAT_ISOLANT = create_material(
    {
        "name": "MAT_ISOLANT",
        "description": "Glue",
        "nuance": "unknow",
        "t_ref": 20,
        "volumic_mass": 2e3,
        "specific_heat": 380,
        "alpha": 0,
        "electrical_conductivity": 0,
        "thermal_conductivity": 1.2,
        "magnet_permeability": 1,
        "young": 2.1e9,
        "poisson": 0.21,
        "expansion_coefficient": 9e-6,
        "rpe": 0,
    }
)

# Get parts from previous defs

M9_M19020601 = query_site("M9_M19020601")
HTS = create_material(
    {
        "name": "HTS",
        "nuance": "HTS",
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

NOUGAT = create_part(
    {"name": "Nougat", "type": "supra", "geometry": "Nougat", "status": "in_study", "material": HTS}
)

MNOUGAT = create_magnet(
    {
        "name": "Nougat",
        "parts": [NOUGAT],
        "status": "in_study",
        "type": MagnetType.SUPRAS,
        "design_office_reference": "Nougat",
        "site": M9_M19020601,
    }
)
