"""
Create a basic magnetdb
"""

from os import getenv

from python_magnetdb.models.magnet import MagnetType
from .crud import create_material, create_part, create_magnet, query_site

data_directory = getenv('DATA_DIR')


# Get parts from previous defs

M9_M19020601 = query_site('M9_M19020601')
HTS = create_material({
'name': "HTS",
    'nuance': "HTS",
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 1.e+10,
    'thermal_conductivity': 360,
    'magnet_permeability': 1,
    'young': 127e+9,
    'poisson': 0.335,
    'expansion_coefficient': 18e-6,
    'rpe': 481000000.0
})

NOUGAT = create_part({
    'name': 'Nougat',
    'type': 'supra',
    'geometry': 'Nougat',
    'status': 'in_study',
    'material': HTS
})

MNOUGAT = create_magnet({
    'name': "Nougat",
    'parts': [NOUGAT],
    'status': 'in_study',
    'type': MagnetType.SUPRAS,
    'design_office_reference': 'Nougat',
    'site': M9_M19020601
})


