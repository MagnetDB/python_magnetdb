"""
Create a basic magnetdb
"""

import os
from os import getenv, path

from . import crud
from .crud import create_material, create_part

data_directory = getenv("DATA_DIR")
project_directory = "HL-37"

# Override crud module's project_directory
crud.project_directory = project_directory

print(f"DATA_DIR={data_directory}")
print(f"PROJECT_DIR={project_directory}")


MA24032701 = create_material(
    {
        "name": "MA24032701",
        "nuance": "CuAg2,75",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 52.9e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 127e9,
        "poisson": 0.335,
        "expansion_coefficient": 18e-6,
        "rpe": 490000000.0,
    }
)


H24110501 = create_part(
    {
        "name": "H24110501",
        "type": "helix",
        "status": "in_operation",
        "material": MA24032701,
        "geometry": "HL-37_H1",
        "cad": "HL-37_H1",
        "shape": "HL-37_H1.shape",
        "modelaxi": "HL-37_H1.d",
    }
)

MA24032501 = create_material(
    {
        "name": "MA24032501",
        "nuance": "CuAg2,75",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 52.9e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 127e9,
        "poisson": 0.335,
        "expansion_coefficient": 18e-6,
        "rpe": 490000000.0,
    }
)


H24110801 = create_part(
    {
        "name": "H24110801",
        "type": "helix",
        "status": "in_operation",
        "material": MA24032501,
        "geometry": "HL-37_H2",
        "cad": "HL-37_H2",
        "shape": "HL-37_H2.shape",
        "modelaxi": "HL-37_H2.d",
    }
)
