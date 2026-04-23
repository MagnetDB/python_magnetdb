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

#
MA18040901 = create_material(
    {
        "name": "MA18040901",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 53.2e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "481",
        "nuance": "CuAg5,5",
    }
)
MA17062101 = create_material(
    {
        "name": "MA17062101",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 48.6e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "518",
        "nuance": "CuCrZr",
    }
)
MA15013001 = create_material(
    {
        "name": "MA15013001",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 52.5e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "500",
        "nuance": "CuAg5,5",
    }
)
MA08070801 = create_material(
    {
        "name": "MA08070801",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.15e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "378",
        "nuance": "CuCrZr",
    }
)
MA10011201 = create_material(
    {
        "name": "MA10011201",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.65e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "363",
        "nuance": "CuCrZr",
    }
)
MA08070810 = create_material(
    {
        "name": "MA08070810",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.6e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "359",
        "nuance": "CuCrZr",
    }
)
MA08070811 = create_material(
    {
        "name": "MA08070811",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.6e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "361",
        "nuance": "CuCrZr",
    }
)
MA08060606 = create_material(
    {
        "name": "MA08060606",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.95e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "358",
        "nuance": "CuCrZr",
    }
)
MA08060607 = create_material(
    {
        "name": "MA08060607",
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
MA08060608 = create_material(
    {
        "name": "MA08060608",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 47.2e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "359",
        "nuance": "CuCrZr",
    }
)
MA08060609 = create_material(
    {
        "name": "MA08060609",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 48.2e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "368",
        "nuance": "CuCrZr",
    }
)
MA10011501 = create_material(
    {
        "name": "MA10011501",
        "description": "",
        "t_ref": 293,
        "volumic_mass": 9000.0,
        "specific_heat": 380,
        "alpha": 0.0036,
        "electrical_conductivity": 50.25e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117000000000.0,
        "poisson": 0.33,
        "expansion_coefficient": 1.8e-05,
        "rpe": "373",
        "nuance": "CuCrZr",
    }
)

H18040901 = create_part(
    {
        "name": "H18040901",
        "type": "helix",
        "status": "in_study",
        "material": MA18040901,
        "geometry": "HL-31_H3",
        "cad": "HL-31_H2",
    }
)
H17062101 = create_part(
    {
        "name": "H17062101",
        "type": "helix",
        "status": "in_study",
        "material": MA17062101,
        "geometry": "HL-31_H4",
        "cad": "HL-31_H3",
    }
)
H15013001 = create_part(
    {
        "name": "H15013001",
        "type": "helix",
        "status": "in_study",
        "material": MA15013001,
        "geometry": "HL-31_H5",
        "cad": "HL-31_H4",
    }
)
H08070801 = create_part(
    {
        "name": "H08070801",
        "type": "helix",
        "status": "in_study",
        "material": MA08070801,
        "geometry": "HL-31_H6",
        "cad": "HL-31_H5",
    }
)
H10011201 = create_part(
    {
        "name": "H10011201",
        "type": "helix",
        "status": "in_study",
        "material": MA10011201,
        "geometry": "HL-31_H7",
        "cad": "HL-31_H6",
    }
)
H08070810 = create_part(
    {
        "name": "H08070810",
        "type": "helix",
        "status": "in_study",
        "material": MA08070810,
        "geometry": "HL-31_H8",
        "cad": "HL-31_H7",
    }
)
H08070811 = create_part(
    {
        "name": "H08070811",
        "type": "helix",
        "status": "in_study",
        "material": MA08070811,
        "geometry": "HL-31_H9",
        "cad": "HL-31_H8",
    }
)
H08060606 = create_part(
    {
        "name": "H08060606",
        "type": "helix",
        "status": "in_study",
        "material": MA08060606,
        "geometry": "HL-31_H10",
        "cad": "HL-31_H9",
    }
)
H08060607 = create_part(
    {
        "name": "H08060607",
        "type": "helix",
        "status": "in_study",
        "material": MA08060607,
        "geometry": "HL-31_H11",
        "cad": "HL-31_H10",
    }
)
H08060608 = create_part(
    {
        "name": "H08060608",
        "type": "helix",
        "status": "in_study",
        "material": MA08060608,
        "geometry": "HL-31_H12",
        "cad": "HL-31_H12",
    }
)
H08060609 = create_part(
    {
        "name": "H08060609",
        "type": "helix",
        "status": "in_study",
        "material": MA08060609,
        "geometry": "HL-31_H13",
        "cad": "HL-31_H13",
    }
)
H10011501 = create_part(
    {
        "name": "H10011501",
        "type": "helix",
        "status": "in_study",
        "material": MA10011501,
        "geometry": "HL-31_H14",
        "cad": "HL-31_H14",
    }
)

# Add Rings
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

# TODO add inner_H2, outer
M10_M19071101 = create_site(
    {"name": "M10_M19071101", "status": "in_study", "config": "MAGFILEM19071101M9Phi50.conf"}
)
M19071101 = create_magnet(
    {
        "name": "M19071101",
        "status": "in_study",
        "type": MagnetType.INSERT,
        "site": M10_M19071101,
        "geometry": "H12-phi50",
        "parts": [
            H18040901,
            H17062101,
            H15013001,
            H08070801,
            H10011201,
            H08070810,
            H08070811,
            H08060606,
            H08060607,
            H08060608,
            H08060609,
            H10011501,
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
        ],
    }
)
