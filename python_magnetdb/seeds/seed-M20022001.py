"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet
from .crud import query_part, query_material
from python_magnetdb.models.magnet import MagnetType

data_directory = getenv("DATA_DIR")


# Material
MA19020601 = create_material(
    {
        "name": "MA19020601",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 53.0e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "500",
        "nuance": "CuAg5,5",
    }
)
MA19022701 = create_material(
    {
        "name": "MA19022701",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 53.4e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "500",
        "nuance": "CuAg5,5",
    }
)

H19020601 = create_part(
    {
        "name": "H19020601",
        "type": "helix",
        "status": "in_study",
        "material": MA19020601,
        "geometry": "HL-31_H12",
        "cad": "HL-31_H12",
    }
)
H19022701 = create_part(
    {
        "name": "H19022701",
        "type": "helix",
        "status": "in_study",
        "material": MA19022701,
        "geometry": "HL-31_H13",
        "cad": "HL-31_H13",
    }
)

MA18101201 = query_material("MA18101201")
MA18110501 = query_material("MA18110501")
MA19012101 = query_material("MA19012101")
MA19011601 = query_material("MA19011601")

H18101201 = create_part(
    {
        "name": "H18101201",
        "type": "helix",
        "status": "in_study",
        "material": MA18101201,
        "geometry": "HL-31_H9",
        "cad": "HL-31_H9",
    }
)
H18110501 = create_part(
    {
        "name": "H18110501",
        "type": "helix",
        "status": "in_study",
        "material": MA18110501,
        "geometry": "HL-31_H10",
        "cad": "HL-31_H10",
    }
)
H19012101 = create_part(
    {
        "name": "H19012101 ",
        "type": "helix",
        "status": "in_study",
        "material": MA19012101,
        "geometry": "HL-31_H11",
        "cad": "HL-31_H11",
    }
)
H19011601 = create_part(
    {
        "name": "H19011601",
        "type": "helix",
        "status": "in_study",
        "material": MA19011601,
        "geometry": "HL-31_H12",
        "cad": "HL-31_H12",
    }
)

H15101601 = query_part("H15101601")
H15061703 = query_part("H15061703")
H15061801 = query_part("H15061801")
H15100501 = query_part("H15100501")
H15101501 = query_part("H15101501")
H18060101 = query_part("H18060101")
H18012501 = query_part("H18012501")
H18051801 = query_part("H18051801")
M19061901_R1 = query_part("M19061901_R1")
M19061901_R2 = query_part("M19061901_R2")
M19061901_R3 = query_part("M19061901_R3")
M19061901_R4 = query_part("M19061901_R4")
M19061901_R5 = query_part("M19061901_R5")
M19061901_R6 = query_part("M19061901_R6")
M19061901_R7 = query_part("M19061901_R7")
M19061901_R8 = query_part("M19061901_R8")
M19061901_R9 = query_part("M19061901_R9")
M19061901_R10 = query_part("M19061901_R10")
M19061901_R11 = query_part("M19061901_R11")
M19061901_R12 = query_part("M19061901_R12")
M19061901_R13 = query_part("M19061901_R13")
M19061901_iL1 = query_part("M19061901_iL1")
M19061901_oL2 = query_part("M19061901_oL2")

M9_M20022001 = create_site(
    {"name": "M9_M20022001", "status": "in_study", "config": "MAGFILEM20022001b.conf"}
)
M20022001 = create_magnet(
    {
        "name": "M20022001",
        "status": "in_study",
        "type": MagnetType.INSERT,
        "site": M9_M20022001,
        "geometry": "HL-31",
        "parts": [
            H15101601,
            H15061703,
            H15061801,
            H15100501,
            H15101501,
            H18060101,
            H18012501,
            H18051801,
            H18101201,
            H18110501,
            H19012101,
            H19011601,
            H19020601,
            H19022701,
            M19061901_R1,
            M19061901_R2,
            M19061901_R3,
            M19061901_R4,
            M19061901_R5,
            M19061901_R6,
            M19061901_R7,
            M19061901_R8,
            M19061901_R9,
            M19061901_R10,
            M19061901_R11,
            M19061901_R12,
            M19061901_R13,
            M19061901_iL1,
            M19061901_oL2,
        ],
    }
)
