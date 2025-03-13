"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet
from .crud import query_part, query_material
from python_magnetdb.models.magnet import MagnetType

data_directory = getenv('DATA_DIR')

# Get parts from previous defs
H15101601 = query_part('H15101601')
print(f'H15101601 ({type(H15101601)}):', H15101601.name)

H15061703 = query_part('H15061703')
print(H15061703.name)

H15061801 = query_part('H15061801')
H15100501 = query_part('H15100501')
H15101501 = query_part('H15101501')
H18060101 = query_part('H18060101')
H18012501 = query_part('H18012501')
H18051801 = query_part('H18051801')
H10061702 = query_part('H10061702')

M19061901_iL1 = query_part('M19061901_iL1')
M19061901_oL2 = query_part('M19061901_oL2')

M19061901_R1 = query_part('M19061901_R1')
M19061901_R2 = query_part('M19061901_R2')
M19061901_R3 = query_part('M19061901_R3')
M19061901_R4 = query_part('M19061901_R4')
M19061901_R5 = query_part('M19061901_R5')
M19061901_R6 = query_part('M19061901_R6')
M19061901_R7 = query_part('M19061901_R7')
M19061901_R8 = query_part('M19061901_R8')
M19061901_R9 = query_part('M19061901_R9')
M19061901_R10 = query_part('M19061901_R10')
M19061901_R11 = query_part('M19061901_R11')
M19061901_R12 = query_part('M19061901_R12')
M19061901_R13 = query_part('M19061901_R13')

# Materials
MA14061901 = create_material({'name': 'MA14061901', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 56.1e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '446', 'nuance': 'CuAg0,1'})
MA14062701 = create_material({'name': 'MA14062701', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 55e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '458', 'nuance': 'CuAg0,1'})
MA14062001 = create_material({'name': 'MA14062001', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 56.1e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '446', 'nuance': 'CuAg0,1'})
MA10061701 = create_material({'name': 'MA10061701', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.1e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '362', 'nuance': 'CuCrZr'})
MA14072201 = create_material({'name': 'MA14072201', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 55.4e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '455', 'nuance': 'CuAg0,1'})

H14061901 = create_part({'name': 'H14061901', 'type': 'helix', 'status': 'in_study', 'material': MA14061901, 'geometry': 'HL-31_H9', 'cad': 'HL-31_H9'})
H14062701 = create_part({'name': 'H14062701', 'type': 'helix', 'status': 'in_study', 'material': MA14062701, 'geometry': 'HL-31_H10', 'cad': 'HL-31_H10'})
H14062001 = create_part({'name': 'H14062001', 'type': 'helix', 'status': 'in_study', 'material': MA14062001, 'geometry': 'HL-31_H11', 'cad': 'HL-31_H11'})
H10061701 = create_part({'name': 'H10061701', 'type': 'helix', 'status': 'in_study', 'material': MA10061701, 'geometry': 'HL-31_H12', 'cad': 'HL-31_H12'})
H14072201 = create_part({'name': 'H14072201', 'type': 'helix', 'status': 'in_study', 'material': MA14072201, 'geometry': 'HL-31_H14', 'cad': 'HL-31_H14'})

# Magnet / Site
# 'commissioned_at',
# 'decommissioned_at',

M9_M18110501 = create_site({'name': 'M9_M18110501', 'status': 'in_study', 'config': 'MAGFILEM18110501.conf'})
print('M9_M18110501:', M9_M18110501)
M18110501 = create_magnet({'name': 'M18110501',
                       'status': 'in_study',
                       'site': M9_M18110501,
                       'geometry': 'HL-31',
                       'type': MagnetType.INSERT,
                       'parts': [H15101601, H15061703, H15061801, H15100501, H15101501, H18060101, H18012501, H18051801, H14061901, H14062701, H14062001, H10061701, H10061702, H14072201, M19061901_R1, M19061901_R2, M19061901_R3, M19061901_R4, M19061901_R5, M19061901_R6, M19061901_R7, M19061901_R8, M19061901_R9, M19061901_R10, M19061901_R11, M19061901_R12, M19061901_R13, M19061901_iL1, M19061901_oL2]})
print('M18110501:', M18110501)

#
MA18040901 = create_material({'name': 'MA18040901', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 53.2e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '481', 'nuance': 'CuAg5,5'})
MA17062101 = create_material({'name': 'MA17062101', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 48.6e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '518', 'nuance': 'CuCrZr'})
MA15013001 = create_material({'name': 'MA15013001', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 52.5e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '500', 'nuance': 'CuAg5,5'})
MA08070801 = create_material({'name': 'MA08070801', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.15e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '378', 'nuance': 'CuCrZr'})
MA10011201 = create_material({'name': 'MA10011201', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.65e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '363', 'nuance': 'CuCrZr'})
MA08070810 = create_material({'name': 'MA08070810', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.6e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '359', 'nuance': 'CuCrZr'})
MA08070811 = create_material({'name': 'MA08070811', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.6e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '361', 'nuance': 'CuCrZr'})
MA08060606 = create_material({'name': 'MA08060606', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.95e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '358', 'nuance': 'CuCrZr'})
MA08060607 = create_material({'name': 'MA08060607', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 51.15e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '364', 'nuance': 'CuCrZr'})
MA08060608 = create_material({'name': 'MA08060608', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 47.2e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '359', 'nuance': 'CuCrZr'})
MA08060609 = create_material({'name': 'MA08060609', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 48.2e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '368', 'nuance': 'CuCrZr'})
MA10011501 = create_material({'name': 'MA10011501', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.25e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '373', 'nuance': 'CuCrZr'})

H18040901 = create_part({'name': 'H18040901', 'type': 'helix', 'status': 'in_study', 'material': MA18040901, 'geometry': 'HL-31_H3', 'cad': 'HL-31_H2'})
H17062101 = create_part({'name': 'H17062101', 'type': 'helix', 'status': 'in_study', 'material': MA17062101, 'geometry': 'HL-31_H4', 'cad': 'HL-31_H3'})
H15013001 = create_part({'name': 'H15013001', 'type': 'helix', 'status': 'in_study', 'material': MA15013001, 'geometry': 'HL-31_H5', 'cad': 'HL-31_H4'})
H08070801 = create_part({'name': 'H08070801', 'type': 'helix', 'status': 'in_study', 'material': MA08070801, 'geometry': 'HL-31_H6', 'cad': 'HL-31_H5'})
H10011201 = create_part({'name': 'H10011201', 'type': 'helix', 'status': 'in_study', 'material': MA10011201, 'geometry': 'HL-31_H7', 'cad': 'HL-31_H6'})
H08070810 = create_part({'name': 'H08070810', 'type': 'helix', 'status': 'in_study', 'material': MA08070810, 'geometry': 'HL-31_H8', 'cad': 'HL-31_H7'})
H08070811 = create_part({'name': 'H08070811', 'type': 'helix', 'status': 'in_study', 'material': MA08070811, 'geometry': 'HL-31_H9', 'cad': 'HL-31_H8'})
H08060606 = create_part({'name': 'H08060606', 'type': 'helix', 'status': 'in_study', 'material': MA08060606, 'geometry': 'HL-31_H10', 'cad': 'HL-31_H9'})
H08060607 = create_part({'name': 'H08060607', 'type': 'helix', 'status': 'in_study', 'material': MA08060607, 'geometry': 'HL-31_H11', 'cad': 'HL-31_H10'})
H08060608 = create_part({'name': 'H08060608', 'type': 'helix', 'status': 'in_study', 'material': MA08060608, 'geometry': 'HL-31_H12', 'cad': 'HL-31_H12'})
H08060609 = create_part({'name': 'H08060609', 'type': 'helix', 'status': 'in_study', 'material': MA08060609, 'geometry': 'HL-31_H13', 'cad': 'HL-31_H13'})
H10011501 = create_part({'name': 'H10011501', 'type': 'helix', 'status': 'in_study', 'material': MA10011501, 'geometry': 'HL-31_H14', 'cad': 'HL-31_H14'})

# TODO add inner_H2, outer
M10_M19071101 = create_site({'name': 'M10_M19071101', 'status': 'in_study', 'config': 'MAGFILEM19071101M9Phi50.conf'})
M19071101 = create_magnet({'name': 'M19071101', 'status': 'in_study', 'type': MagnetType.INSERT, 'site': M10_M19071101, 'geometry': 'H12-phi50', 'parts': [H18040901, H17062101, H15013001, H08070801, H10011201, H08070810, H08070811, H08060606, H08060607, H08060608, H08060609, H10011501, M19061901_R3, M19061901_R4, M19061901_R5, M19061901_R6, M19061901_R7, M19061901_R8, M19061901_R9, M19061901_R10, M19061901_R11, M19061901_R12, M19061901_R13]})

# Material
MA19020601 = create_material({'name': 'MA19020601', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 53.0e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '500', 'nuance': 'CuAg5,5'})
MA19022701 = create_material({'name': 'MA19022701', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 53.4e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '500', 'nuance': 'CuAg5,5'})

H19020601 = create_part({'name': 'H19020601', 'type': 'helix', 'status': 'in_study', 'material': MA19020601, 'geometry': 'HL-31_H12', 'cad': 'HL-31_H12'})
H19022701 = create_part({'name': 'H19022701', 'type': 'helix', 'status': 'in_study', 'material': MA19022701, 'geometry': 'HL-31_H13', 'cad': 'HL-31_H13'})

MA18101201 = query_material('MA18101201')
MA18110501 = query_material('MA18110501')
MA19012101 = query_material('MA19012101')
MA19011601 = query_material('MA19011601')

H18101201 = create_part({'name': 'H18101201', 'type': 'helix', 'status': 'in_study', 'material': MA18101201, 'geometry': 'HL-31_H9', 'cad': 'HL-31_H9'})
H18110501 = create_part({'name': 'H18110501', 'type': 'helix', 'status': 'in_study', 'material': MA18110501, 'geometry': 'HL-31_H10', 'cad': 'HL-31_H10'})
H19012101 = create_part({'name': 'H19012101 ', 'type': 'helix', 'status': 'in_study', 'material': MA19012101, 'geometry': 'HL-31_H11', 'cad': 'HL-31_H11'})
H19011601 = create_part({'name': 'H19011601', 'type': 'helix', 'status': 'in_study', 'material': MA19011601, 'geometry': 'HL-31_H12', 'cad': 'HL-31_H12'})

M9_M20022001 = create_site({'name': 'M9_M20022001', 'status': 'in_study', 'config': 'MAGFILEM20022001b.conf'})
M20022001 = create_magnet({'name': 'M20022001', 'status': 'in_study', 'type': MagnetType.INSERT, 'site': M9_M20022001, 'geometry': 'HL-31', 'parts': [H15101601, H15061703, H15061801, H15100501, H15101501, H18060101, H18012501, H18051801, H18101201, H18110501, H19012101, H19011601, H19020601, H19022701, M19061901_R1, M19061901_R2, M19061901_R3, M19061901_R4, M19061901_R5, M19061901_R6, M19061901_R7, M19061901_R8, M19061901_R9, M19061901_R10, M19061901_R11, M19061901_R12, M19061901_R13, M19061901_iL1, M19061901_oL2]})

# Material
M9_M22011801 = create_site({'name': 'M9_M22011801', 'status': 'in_study', 'config': 'MAGFILEM22011801.conf'})
M22011801 = create_magnet({'name': 'M22011801', 'status': 'in_study', 'type': MagnetType.INSERT, 'site': M9_M22011801, 'geometry': 'HL-31', 'parts': [H15101601, H15061703, H15061801, H15100501, H15101501, H18060101, H18012501, H18051801, H18101201, H18110501, H19012101, H19011601, H19020601, H14072201, M19061901_R1, M19061901_R2, M19061901_R3, M19061901_R4, M19061901_R5, M19061901_R6, M19061901_R7, M19061901_R8, M19061901_R9, M19061901_R10, M19061901_R11, M19061901_R12, M19061901_R13, M19061901_iL1, M19061901_oL2]})

M9_M19020601 = create_site({'name': 'M9_M19020601', 'status': 'in_study', 'config': 'MAGFILEM2021.10.11.conf'})
#MA10061703 = create_material({'name': 'MA10061703', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.25e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '373', 'nuance': 'CuCrZr'})
#MA10061702 = create_material({'name': 'MA10061702', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 46.5e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '366', 'nuance': 'CuCrZr'})
#MA10061701 = create_material({'name': 'MA10061701', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.1e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '362', 'nuance': 'CuCrZr'})
MA09031205 = create_material({'name': 'MA09031205', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 51.15e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '364', 'nuance': 'CuCrZr'})
MA09031204 = create_material({'name': 'MA09031204', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 50.2e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '363', 'nuance': 'CuCrZr'})
MA18090401 = create_material({'name': 'MA18090401', 'description': '', 't_ref': 293, 'volumic_mass': 9000.0, 'specific_heat': 380, 'alpha': 0.0036, 'electrical_conductivity': 53.6e+6, 'thermal_conductivity': 380, 'magnet_permeability': 1, 'young': 117000000000.0, 'poisson': 0.33, 'expansion_coefficient': 1.8e-05, 'rpe': '511', 'nuance': 'CuAg5.5'})
H18090401 = create_part({'name': 'H18090401', 'type': 'helix', 'status': 'in_study', 'material': MA18090401, 'geometry': 'HL-31_H9', 'cad': 'HL-31_H9'})
H09031204 = create_part({'name': 'H09031204', 'type': 'helix', 'status': 'in_study', 'material': MA09031204, 'geometry': 'HL-31_H10', 'cad': 'HL-31_H10'})
H09031205 = create_part({'name': 'H09031205', 'type': 'helix', 'status': 'in_study', 'material': MA09031205, 'geometry': 'HL-31_H11', 'cad': 'HL-31_H11'})
#H10061701 = create_part({'name': 'H10061701', 'type': 'helix', 'status': 'in_study', 'material': MA10061701, 'geometry': 'HL-31_H12', 'cad': 'HL-31_H12'})
#H10061702 = create_part({'name': 'H10061702', 'type': 'helix', 'status': 'in_study', 'material': MA10061702, 'geometry': 'HL-31_H13', 'cad': 'HL-31_H13'})
#H10061703 = create_part({'name': 'H10061703', 'type': 'helix', 'status': 'in_study', 'material': MA10061703, 'geometry': 'HL-31_H14', 'cad': 'HL-31_H14'})
H10061702 = query_part('H10061702')
H10061703 = query_part('H10061703')

MAT_LEAD = query_material('MAT_LEAD')
M19020601_iL1 = create_part({
'name': 'M19020601_iL1',
    'type': 'lead',
    'status': 'in_study',
    'material': MAT_LEAD,
    'geometry': 'inner-Nougat',
    'cad': 'Inner-Nougat',
})
M19020601 = create_magnet({'name': 'M19020601', 'status': 'in_study', 'type': MagnetType.INSERT, 'site': M9_M19020601, 'geometry': 'H6-phi170', 'parts': [H18090401, H09031204, H09031205, H10061701, H10061702, H10061703, M19061901_R9, M19061901_R10, M19061901_R11, M19061901_R12, M19061901_R13, M19020601_iL1, M19061901_oL2]})

