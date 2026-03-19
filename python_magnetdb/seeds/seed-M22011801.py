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

H15101601 = query_part("H15101601")
H15061703 = query_part("H15061703")
H15061801 = query_part("H15061801")
H15100501 = query_part("H15100501")
H15101501 = query_part("H15101501")
H18060101 = query_part("H18060101")
H18012501 = query_part("H18012501")
H18051801 = query_part("H18051801")
H18101201 = query_part("H18101201")
H18110501 = query_part("H18110501")
H19012101 = query_part("H19012101")
H19011601 = query_part("H19011601")
H19020601 = query_part("H19020601")
H14072201 = query_part("H14072201")
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

# Material
M9_M22011801 = create_site(
    {"name": "M9_M22011801", "status": "in_study", "config": "MAGFILEM22011801.conf"}
)
M22011801 = create_magnet(
    {
        "name": "M22011801",
        "status": "in_study",
        "type": MagnetType.INSERT,
        "site": M9_M22011801,
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
            H14072201,
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
