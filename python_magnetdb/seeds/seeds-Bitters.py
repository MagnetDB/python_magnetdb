"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_magnet
from ..models.magnet import MagnetType

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

CUAG01 = create_material(
    {
        "name": "CuAg01",
        "nuance": "CuAg01",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 50.1e6,
        "thermal_conductivity": 360,
        "magnet_permeability": 1,
        "young": 127e9,
        "poisson": 0.335,
        "expansion_coefficient": 18e-6,
        "rpe": 481000000.0,
    }
)

M9BI = create_part(
    {
        "name": "M9Bi",
        "type": "bitter",
        "design_office_reference": "BI-03-002-A",
        "status": "in_study",
        "material": CUAG01,
        "geometry": "M9_Bi",
    }
)

M9BE = create_part(
    {
        "name": "M9Be",
        "type": "bitter",
        "design_office_reference": "BE-03-002-A",
        "geometry": "M9_Be",
        "status": "in_study",
        "material": CUAG01,
    }
)

M9BITTERS = create_magnet(
    {
        "name": "M9Bitters",
        "status": "in_study",
        "parts": [M9BI, M9BE],
        "geometry": "M9Bitters",
        "type": MagnetType.BITTERS,
        "design_office_reference": "M9Bitters",
    }
)

M10BI = create_part(
    {
        "name": "M10Bi",
        "type": "bitter",
        "design_office_reference": "BI-03-002-A",
        "geometry": "M10_Bi",
        "status": "in_study",
        "material": CUAG01,
    }
)

M10BE = create_part(
    {
        "name": "M10Be",
        "type": "bitter",
        "design_office_reference": "BE-03-002-A",
        "geometry": "M10_Be",
        "status": "in_study",
        "material": CUAG01,
    }
)

M10BITTERS = create_magnet(
    {
        "name": "M10Bitters",
        "status": "in_study",
        "parts": [M10BI, M10BE],
        "type": MagnetType.BITTERS,
        "geometry": "M10Bitters",
        "design_office_reference": "M10Bitters",
    }
)

CUAG008 = create_material(
    {
        "name": "B_CuAg008",
        "nuance": "CuAg008",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 50.1e6,
        "thermal_conductivity": 360,
        "magnet_permeability": 1,
        "young": 127e9,
        "poisson": 0.335,
        "expansion_coefficient": 18e-6,
        "rpe": 481000000.0,
    }
)

M8BI = create_part(
    {
        "name": "M8Bi",
        "type": "bitter",
        "design_office_reference": "BI-03-002-A",
        "geometry": "M8_Bi",
        "status": "in_study",
        "material": CUAG008,
    }
)

M8BE = create_part(
    {
        "name": "M8Be",
        "type": "bitter",
        "design_office_reference": "BE-03-002-A",
        "geometry": "M8_Be",
        "status": "in_study",
        "material": CUAG008,
    }
)

M8BITTERS = create_magnet(
    {
        "name": "M8Bitters",
        "status": "in_study",
        "parts": [M8BI, M8BE],
        "type": MagnetType.BITTERS,
        "design_office_reference": "M8Bitters",
    }
)
