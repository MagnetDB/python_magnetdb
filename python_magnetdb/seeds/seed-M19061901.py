"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet
from ..models.magnet import MagnetType

data_directory = getenv("DATA_DIR")

MA15101601 = create_material(
    {
        "name": "MA15101601",
        "description": "H1",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 52.4e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 481,
    }
)
MA15061703 = create_material(
    {
        "name": "MA15061703",
        "description": "H2",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.3e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 482,
    }
)
MA15061801 = create_material(
    {
        "name": "MA15061801",
        "description": "H3",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 52.6e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 496,
    }
)
MA15100501 = create_material(
    {
        "name": "MA15100501",
        "description": "H4",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 52.8e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 508,
    }
)
MA15101501 = create_material(
    {
        "name": "MA15101501",
        "description": "H5",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.1e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 506,
    }
)
MA18060101 = create_material(
    {
        "name": "MA18060101",
        "description": "H6",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.2e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 512,
    }
)
MA18012501 = create_material(
    {
        "name": "MA18012501",
        "description": "H7",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.1e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 500,
    }
)
MA18051801 = create_material(
    {
        "name": "MA18051801",
        "description": "H8",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 51.9e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 512,
    }
)
MA18101201 = create_material(
    {
        "name": "MA18101201",
        "description": "H9",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.7e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 500,
    }
)
MA18110501 = create_material(
    {
        "name": "MA18110501",
        "description": "H10",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.3e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 500,
    }
)
MA19012101 = create_material(
    {
        "name": "MA19012101",
        "description": "H11",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.8e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 500,
    }
)
MA19011601 = create_material(
    {
        "name": "MA19011601",
        "description": "H12",
        "nuance": "CuAg5.5",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.6e-3,
        "electrical_conductivity": 53.2e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 500,
    }
)
MA10061702 = create_material(
    {
        "name": "MA10061702",
        "description": "H13",
        "nuance": "CuCrZr",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.4e-3,
        "electrical_conductivity": 46.5e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 366,
    }
)
MA10061703 = create_material(
    {
        "name": "MA10061703",
        "description": "H14",
        "nuance": "CuCrZr",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.4e-3,
        "electrical_conductivity": 50.25e6,
        "thermal_conductivity": 380,
        "magnet_permeability": 1,
        "young": 117e9,
        "poisson": 0.33,
        "expansion_coefficient": 18e-6,
        "rpe": 373,
    }
)

MAT1_RING = create_material(
    {
        "name": "MAT1_RING",
        "description": "R1, R2",
        "nuance": "unknow",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.4e-3,
        "electrical_conductivity": 41e6,
        "thermal_conductivity": 320,
        "magnet_permeability": 1,
        "young": 131e9,
        "poisson": 0.3,
        "expansion_coefficient": 17e-6,
        "rpe": 0,
    }
)
MAT2_RING = create_material(
    {
        "name": "MAT2_RING",
        "description": "R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13",
        "nuance": "unknow",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.4e-3,
        "electrical_conductivity": 50e6,
        "thermal_conductivity": 320,
        "magnet_permeability": 1,
        "young": 131e9,
        "poisson": 0.3,
        "expansion_coefficient": 17e-6,
        "rpe": 0,
    }
)
MAT_LEAD = create_material(
    {
        "name": "MAT_LEAD",
        "description": "il1 ol2",
        "nuance": "unknow",
        "t_ref": 293,
        "volumic_mass": 9e3,
        "specific_heat": 380,
        "alpha": 3.4e-3,
        "electrical_conductivity": 58.0e6,
        "thermal_conductivity": 390,
        "magnet_permeability": 1,
        "young": 131e9,
        "poisson": 0.3,
        "expansion_coefficient": 17e-6,
        "rpe": 0,
    }
)
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

H15101601 = create_part(
    {
        "name": "H15101601",
        "type": "helix",
        "status": "in_operation",
        "material": MA15101601,
        "geometry": "HL-31_H1",
        "cad": "HL-31_H1",
    }
)
H15061703 = create_part(
    {
        "name": "H15061703",
        "type": "helix",
        "status": "in_operation",
        "material": MA15061703,
        "geometry": "HL-31_H2",
        "cad": "HL-31_H2",
    }
)
H15061801 = create_part(
    {
        "name": "H15061801",
        "type": "helix",
        "status": "in_operation",
        "material": MA15061801,
        "geometry": "HL-31_H3",
        "cad": "HL-31_H3",
    }
)
H15100501 = create_part(
    {
        "name": "H15100501",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-008-A",
        "cad": "HL-31_H4",
        "geometry": "HL-31_H4",
        "material": MA15100501,
    }
)
H15101501 = create_part(
    {
        "name": "H15101501",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0010-A",
        "geometry": "HL-31_H5",
        "cad": "HL-31_H5",
        "material": MA15101501,
    }
)
H18060101 = create_part(
    {
        "name": "H18060101",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0012-A",
        "geometry": "HL-31_H6",
        "cad": "HL-31_H6",
        "material": MA18060101,
    }
)
H18012501 = create_part(
    {
        "name": "H18012501",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0014-A",
        "geometry": "HL-31_H7",
        "cad": "HL-31_H7",
        "material": MA18012501,
    }
)
H18051801 = create_part(
    {
        "name": "H18051801",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0016-A",
        "geometry": "HL-31_H8",
        "cad": "HL-31_H8",
        "material": MA18051801,
    }
)
H19060601 = create_part(
    {
        "name": "H19060601",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0018",
        "geometry": "HL-31_H9",
        "cad": "HL-31_H9",
        "material": MA18101201,
    }
)
H19060602 = create_part(
    {
        "name": "H19060602",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0020",
        "geometry": "HL-31_H10",
        "cad": "HL-31_H10",
        "material": MA18110501,
    }
)
H19061201 = create_part(
    {
        "name": "H19061201",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0022",
        "geometry": "HL-31_H11",
        "cad": "HL-31_H11",
        "material": MA19012101,
    }
)
H19060603 = create_part(
    {
        "name": "H19060603",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HL-34-0024",
        "geometry": "HL-31_H12",
        "cad": "HL-31_H12",
        "material": MA19011601,
    }
)
H10061702 = create_part(
    {
        "name": "H10061702",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HR-21-126-A",
        "geometry": "HL-31_H13",
        "cad": "HL-31_H13",
        "material": MA10061702,
    }
)
H10061703 = create_part(
    {
        "name": "H10061703",
        "type": "helix",
        "status": "in_study",
        "design_office_reference": "HR-21-128-A",
        "geometry": "HL-31_H14",
        "cad": "HL-31_H14",
        "material": MA10061703,
    }
)

M19061901_R1 = create_part(
    {
        "name": "M19061901_R1",
        "type": "ring",
        "status": "in_operation",
        "material": MAT1_RING,
        "geometry": "Ring-H1H2",
        "cad": "Ring-H1H2",
    }
)
M19061901_R2 = create_part(
    {
        "name": "M19061901_R2",
        "type": "ring",
        "status": "in_operation",
        "material": MAT1_RING,
        "geometry": "Ring-H2H3",
        "cad": "Ring-H2H3",
    }
)
M19061901_R3 = create_part(
    {
        "name": "M19061901_R3",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H3H4",
        "cad": "Ring-H3H4",
    }
)
M19061901_R4 = create_part(
    {
        "name": "M19061901_R4",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H4H5",
        "cad": "Ring-H4H5",
    }
)
M19061901_R5 = create_part(
    {
        "name": "M19061901_R5",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H5H6",
        "cad": "Ring-H5H6",
    }
)
M19061901_R6 = create_part(
    {
        "name": "M19061901_R6",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H6H7",
        "cad": "Ring-H6H7",
    }
)
M19061901_R7 = create_part(
    {
        "name": "M19061901_R7",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H7H8",
        "cad": "Ring-H7H8",
    }
)
M19061901_R8 = create_part(
    {
        "name": "M19061901_R8",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H8H9",
        "cad": "Ring-H8H9",
    }
)
M19061901_R9 = create_part(
    {
        "name": "M19061901_R9",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H9H10",
        "cad": "Ring-H9H10",
    }
)
M19061901_R10 = create_part(
    {
        "name": "M19061901_R10",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H10H11",
        "cad": "Ring-H10H11",
    }
)
M19061901_R11 = create_part(
    {
        "name": "M19061901_R11",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H11H12",
        "cad": "Ring-H11H12",
    }
)
M19061901_R12 = create_part(
    {
        "name": "M19061901_R12",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H12H13",
        "cad": "Ring-H12H13",
    }
)
M19061901_R13 = create_part(
    {
        "name": "M19061901_R13",
        "type": "ring",
        "status": "in_study",
        "material": MAT2_RING,
        "geometry": "Ring-H13H14",
        "cad": "Ring-H13H14",
    }
)

M19061901_iL1 = create_part(
    {
        "name": "M19061901_iL1",
        "type": "lead",
        "status": "in_operation",
        "material": MAT_LEAD,
        "geometry": "inner",
        "cad": "Inner",
    }
)
M19061901_oL2 = create_part(
    {
        "name": "M19061901_oL2",
        "type": "lead",
        "status": "in_operation",
        "material": MAT_LEAD,
        "geometry": "outer-H14",
        "cad": "Outer-H14",
    }
)


M9_M19061901 = create_site(
    {
        "name": "M9_M19061901",
        "status": "in_study",
        # 'config': 'MAGFILEM19061901.conf', # TODO MagConfile instead
    }
)

M19061901 = create_magnet(
    {
        "name": "M19061901",
        "geometry": "HL-31",
        "type": MagnetType.INSERT,
        "status": "in_study",
        "parts": [
            H15101601,
            H15061703,
            H15061801,
            H15100501,
            H15101501,
            H18060101,
            H18012501,
            H18051801,
            H19060601,
            H19060602,
            H19061201,
            H19060603,
            H10061702,
            H10061703,
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
        "site": M9_M19061901,
    }
)
