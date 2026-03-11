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

# Get parts from previous defs
H15101601 = query_part("H15101601")
print(f"H15101601 ({type(H15101601)}):", H15101601.name)

H15061703 = query_part("H15061703")
print(H15061703.name)

H15061801 = query_part("H15061801")
H15100501 = query_part("H15100501")
H15101501 = query_part("H15101501")
H18060101 = query_part("H18060101")
H18012501 = query_part("H18012501")
H18051801 = query_part("H18051801")
H10061702 = query_part("H10061702")

M19061901_iL1 = query_part("M19061901_iL1")
M19061901_oL2 = query_part("M19061901_oL2")

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

# Materials
MA14061901 = create_material(
    {
        "name": "MA14061901",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 56.1e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "446",
        "nuance": "CuAg0,1",
    }
)
MA14062701 = create_material(
    {
        "name": "MA14062701",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 55e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "458",
        "nuance": "CuAg0,1",
    }
)
MA14062001 = create_material(
    {
        "name": "MA14062001",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 56.1e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "446",
        "nuance": "CuAg0,1",
    }
)
MA10061701 = create_material(
    {
        "name": "MA10061701",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.1e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "362",
        "nuance": "CuCrZr",
    }
)
MA14072201 = create_material(
    {
        "name": "MA14072201",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 55.4e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "455",
        "nuance": "CuAg0,1",
    }
)

H14061901 = create_part(
    {
        "name": "H14061901",
        "type": "helix",
        "status": "in_study",
        "material": MA14061901,
        "geometry": "HL-31_H9",
        "cad": "HL-31_H9",
    }
)
H14062701 = create_part(
    {
        "name": "H14062701",
        "type": "helix",
        "status": "in_study",
        "material": MA14062701,
        "geometry": "HL-31_H10",
        "cad": "HL-31_H10",
    }
)
H14062001 = create_part(
    {
        "name": "H14062001",
        "type": "helix",
        "status": "in_study",
        "material": MA14062001,
        "geometry": "HL-31_H11",
        "cad": "HL-31_H11",
    }
)
H10061701 = create_part(
    {
        "name": "H10061701",
        "type": "helix",
        "status": "in_study",
        "material": MA10061701,
        "geometry": "HL-31_H12",
        "cad": "HL-31_H12",
    }
)
H14072201 = create_part(
    {
        "name": "H14072201",
        "type": "helix",
        "status": "in_study",
        "material": MA14072201,
        "geometry": "HL-31_H14",
        "cad": "HL-31_H14",
    }
)

# Magnet / Site
# 'commissioned_at',
# 'decommissioned_at',

M9_M18110501 = create_site(
    {"name": "M9_M18110501", "status": "in_study", "config": "MAGFILEM18110501.conf"}
)
print("M9_M18110501:", M9_M18110501)
M18110501 = create_magnet(
    {
        "name": "M18110501",
        "status": "in_study",
        "site": M9_M18110501,
        "geometry": "HL-31",
        "type": MagnetType.INSERT,
        "parts": [
            H15101601,
            H15061703,
            H15061801,
            H15100501,
            H15101501,
            H18060101,
            H18012501,
            H18051801,
            H14061901,
            H14062701,
            H14062001,
            H10061701,
            H10061702,
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
print("M18110501:", M18110501)
