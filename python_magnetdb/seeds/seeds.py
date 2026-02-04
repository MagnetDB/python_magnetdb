"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet
from ..models.magnet import MagnetType

data_directory = getenv("DATA_DIR")


MAT_TEST1 = create_material(
    {
        "name": "MAT_TEST1",
        "description": "R1, R2",
        "nuance": "Cu5Ag5,08",
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
MAT_TEST2 = create_material(
    {
        "name": "MAT_TEST2",
        "description": "R1, R2",
        "nuance": "Cu5Ag5,08",
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

HLTESTH1 = create_part(
    {
        "name": "HL-34_H1",
        "type": "helix",
        "design_office_reference": "HL-34-001-A",
        "status": "in_operation",
        "material": MAT_TEST1,
        "geometry": "HL-31_H1",
        "cad": "HL-31_H1",
    }
)

HLTESTH2 = create_part(
    {
        "name": "HL-34_H2",
        "type": "helix",
        "design_office_reference": "HL-34-001-A",
        "status": "in_operation",
        "material": MAT_TEST2,
        "geometry": "HL-31_H2",
        "cad": "HL-31_H2",
    }
)
HLTESTR1 = create_part(
    {
        "name": "Ring-H1H2",
        "type": "ring",
        "design_office_reference": "HL-34-001-A",
        "status": "in_operation",
        "material": MAT_TEST2,
        "geometry": "Ring-H1H2",
        "cad": "Ring-H1H2",
    }
)

MTEST = create_site(
    {
        "name": "MTest",
        "status": "in_study",
        # 'config': 'HL-test2-cfpdes-thelec-Axi-sim', # TODO MagConfile instead
    }
)

MTest2 = create_site(
    {
        "name": "MTest2",
        "status": "defunct",
    }
)

HLtest = create_magnet(
    {
        "name": "HL-test",
        "status": "in_study",
        "site": MTEST,
        "parts": [HLTESTH1, HLTESTH2, HLTESTR1],
        "type": MagnetType.INSERT,
        "inner_bore": 18.8,  # mm
        "outer_bore": 31.2,  # mm
    }
)


# Add tore for test
mattore = create_material(
    {
        "name": "mtore",
        "nuance": "test",
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

Tore = create_part(
    {
        "name": "tore",
        "type": "bitter",
        "geometry": "tore",
        "status": "in_study",
        "material": mattore,
    }
)
Tore1 = create_part(
    {
        "name": "tore1",
        "type": "bitter",
        "geometry": "tore",
        "status": "in_study",
        "material": mattore,
    }
)
Tore2 = create_part(
    {
        "name": "tore2",
        "type": "bitter",
        "geometry": "tore",
        "status": "in_study",
        "material": mattore,
    }
)

m_MTore = create_site({"name": "MTore", "status": "in_study"})
MTore = create_magnet(
    {
        "name": "Tore-test",
        "geometry": "MTore",
        "status": "in_study",
        "type": MagnetType.BITTERS,
        "site": m_MTore,
    }
)
