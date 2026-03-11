"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet
from .crud import query_part, query_material
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

MA09031205 = create_material(
    {
        "name": "MA09031205",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 51.15e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "364",
        "nuance": "CuCrZr",
    }
)
MA09031204 = create_material(
    {
        "name": "MA09031204",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.2e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "363",
        "nuance": "CuCrZr",
    }
)
MA18090401 = create_material(
    {
        "name": "MA18090401",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 53.6e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "511",
        "nuance": "CuAg5.5",
    }
)
H18090401 = create_part(
    {
        "name": "H18090401",
        "type": "helix",
        "status": "in_study",
        "material": MA18090401,
        "geometry": "HL-31_H9",
        "cad": "HL-31_H9",
    }
)
H09031204 = create_part(
    {
        "name": "H09031204",
        "type": "helix",
        "status": "in_study",
        "material": MA09031204,
        "geometry": "HL-31_H10",
        "cad": "HL-31_H10",
    }
)
H09031205 = create_part(
    {
        "name": "H09031205",
        "type": "helix",
        "status": "in_study",
        "material": MA09031205,
        "geometry": "HL-31_H11",
        "cad": "HL-31_H11",
    }
)

H10061701 = query_part("H10061701")
H10061702 = query_part("H10061702")
H10061703 = query_part("H10061703")

M19061901_R9 = query_part("M19061901_R9")
M19061901_R10 = query_part("M19061901_R10")
M19061901_R11 = query_part("M19061901_R11")
M19061901_R12 = query_part("M19061901_R12")
M19061901_R13 = query_part("M19061901_R13")

MAT_LEAD = query_material("MAT_LEAD")
M19020601_iL1 = create_part(
    {
        "name": "M19020601_iL1",
        "type": "lead",
        "status": "in_study",
        "material": MAT_LEAD,
        "geometry": "inner-Nougat",
        "cad": "Inner-Nougat",
    }
)
M19061901_oL2 = query_part("M19061901_oL2")
M9_M19020601 = create_site(
    {"name": "M9_M19020601", "status": "in_study", "config": "MAGFILEM2021.10.11.conf"}
)

M19020601 = create_magnet(
    {
        "name": "M19020601",
        "status": "in_study",
        "type": MagnetType.INSERT,
        "site": M9_M19020601,
        "geometry": "H6-phi170",
        "parts": [
            H18090401,
            H09031204,
            H09031205,
            H10061701,
            H10061702,
            H10061703,
            M19061901_R9,
            M19061901_R10,
            M19061901_R11,
            M19061901_R12,
            M19061901_R13,
            M19020601_iL1,
            M19061901_oL2,
        ],
    }
)
