"""
Create a basic magnetdb
"""

from os import getenv

from .crud import create_material, create_part, create_site, create_magnet

data_directory = getenv('DATA_DIR')


MA15101601 = create_material({
    'name': 'MA15101601',
    'description': 'H1',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 52.4e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 481,
})
MA15061703 = create_material({
    'name': 'MA15061703',
    'description': 'H2',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.3e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 482,
})
MA15061801 = create_material({
    'name': 'MA15061801',
    'description': 'H3',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 52.6e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 496,
})
MA15100501 = create_material({
    'name': 'MA15100501',
    'description': 'H4',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 52.8e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 508,
})
MA15101501 = create_material({
    'name': 'MA15101501',
    'description': 'H5',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.1e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 506,
})
MA18060101 = create_material({
    'name': 'MA18060101',
    'description': 'H6',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.2e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 512,
})
MA18012501 = create_material({
    'name': 'MA18012501',
    'description': 'H7',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.1e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 500,
})
MA18051801 = create_material({
    'name': 'MA18051801',
    'description': 'H8',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 51.9e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 512,
})
MA18101201 = create_material({
    'name': 'MA18101201',
    'description': 'H9',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.7e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 500,
})
MA18110501 = create_material({
    'name': 'MA18110501',
    'description': 'H10',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.3e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 500,
})
MA19012101 = create_material({
    'name': 'MA19012101',
    'description': 'H11',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.8e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 500,
})
MA19011601 = create_material({
    'name': 'MA19011601',
    'description': 'H12',
    'nuance': 'CuAg5.5',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.2e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 500,
})
MA10061702 = create_material({
    'name': 'MA10061702',
    'description': 'H13',
    'nuance': 'CuCrZr',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.4e-3,
    'electrical_conductivity': 46.5e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 366,
})
MA10061703 = create_material({
    'name': 'MA10061703',
    'description': 'H14',
    'nuance': 'CuCrZr',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.4e-3,
    'electrical_conductivity': 50.25e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 373,
})
MAT1_RING = create_material({
    'name': 'MAT1_RING',
    'description': 'R1, R2',
    'nuance': 'unknow',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.4e-3,
    'electrical_conductivity': 41e+6,
    'thermal_conductivity': 320,
    'magnet_permeability': 1,
    'young': 131e+9,
    'poisson': 0.3,
    'expansion_coefficient': 17e-6,
    'rpe': 0,
})
MAT2_RING = create_material({
    'name': 'MAT2_RING',
    'description': 'R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13',
    'nuance': 'unknow',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.4e-3,
    'electrical_conductivity': 50e+6,
    'thermal_conductivity': 320,
    'magnet_permeability': 1,
    'young': 131e+9,
    'poisson': 0.3,
    'expansion_coefficient': 17e-6,
    'rpe': 0,
})
MAT_LEAD = create_material({
    'name': 'MAT_LEAD',
    'description': 'il1 ol2',
    'nuance': 'unknow',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.4e-3,
    'electrical_conductivity': 58.0e+6,
    'thermal_conductivity': 390,
    'magnet_permeability': 1,
    'young': 131e+9,
    'poisson': 0.3,
    'expansion_coefficient': 17e-6,
    'rpe': 0,
})
MAT_ISOLANT = create_material({
    'name': 'MAT_ISOLANT',
    'description': 'Glue',
    'nuance': 'unknow',
    't_ref': 20,
    'volumic_mass': 2e+3,
    'specific_heat': 380,
    'alpha': 0,
    'electrical_conductivity': 0,
    'thermal_conductivity': 1.2,
    'magnet_permeability': 1,
    'young': 2.1e9,
    'poisson': 0.21,
    'expansion_coefficient': 9e-6,
    'rpe': 0,
})


H15101601 = create_part({
    'name': 'H15101601',
    'type': 'helix',
    'status': 'in_operation',
    'material': MA15101601,
    'geometry': 'HL-31_H1',
    'cad': 'HL-31_H1',
})
H15061703 = create_part({
    'name': 'H15061703',
    'type': 'helix',
    'status': 'in_operation',
    'material': MA15061703,
    'geometry': 'HL-31_H2',
    'cad': 'HL-31_H2',
})
H15061801 = create_part({
    'name': 'H15061801',
    'type': 'helix',
    'status': 'in_operation',
    'material': MA15061801,
    'geometry': 'HL-31_H3',
    'cad': 'HL-31_H3',
})
H15100501 = create_part({
    'name': 'H15100501',
    'type': 'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-008-A',
    'cad': 'HL-31_H4',
    'geometry': 'HL-31_H4',
    'material': MA15100501
})
H15101501 = create_part({
    'name':'H15101501',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0010-A',
    'geometry': 'HL-31_H5',
    'cad': 'HL-31_H5',
    'material': MA15101501
})
H18060101 = create_part({
    'name':'H18060101',
    'type': 'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0012-A',
    'geometry': 'HL-31_H6',
    'cad': 'HL-31_H6',
    'material':MA18060101
})
H18012501 = create_part({
    'name':'H18012501',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0014-A',
    'geometry': 'HL-31_H7',
    'cad': 'HL-31_H7',
    'material':MA18012501
})
H18051801 = create_part({
    'name':'H18051801',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0016-A',
    'geometry': 'HL-31_H8',
    'cad': 'HL-31_H8',
    'material':MA18051801
})
H19060601 = create_part({
    'name':'H19060601',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0018',
    'geometry': 'HL-31_H9',
    'cad': 'HL-31_H9',
    'material':MA18101201
})
H19060602 = create_part({
    'name':'H19060602',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0020',
    'geometry': 'HL-31_H10',
    'cad': 'HL-31_H10',
    'material':MA18110501
})
H19061201 = create_part({
    'name':'H19061201',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0022',
    'geometry': 'HL-31_H11',
    'cad': 'HL-31_H11',
    'material':MA19012101
})
H19060603 = create_part({
    'name':'H19060603',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HL-34-0024',
    'geometry': 'HL-31_H12',
    'cad': 'HL-31_H12',
    'material':MA19011601
})
H10061702 = create_part({
    'name':'H10061702',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HR-21-126-A',
    'geometry': 'HL-31_H13',
    'cad': 'HL-31_H13',
    'material':MA10061702
})
H10061703 = create_part({
    'name':'H10061703',
    'type':'helix',
    'status': 'in_study',
    'design_office_reference': 'HR-21-128-A',
    'geometry': 'HL-31_H14',
    'cad': 'HL-31_H14',
    'material':MA10061703
})

M19061901_R1 = create_part({
    'name': 'M19061901_R1',
    'type': 'ring',
    'status': 'in_operation',
    'material': MAT1_RING,
    'geometry': 'Ring-H1H2',
    'cad': 'Ring-H1H2',
})
M19061901_R2 = create_part({
    'name': 'M19061901_R2',
    'type': 'ring',
    'status': 'in_operation',
    'material': MAT1_RING,
    'geometry': 'Ring-H2H3',
    'cad': 'Ring-H2H3',
})
M19061901_R3 = create_part({
    'name': 'M19061901_R3',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H3H4',
    'cad': 'Ring-H3H4',
})
M19061901_R4 = create_part({
    'name': 'M19061901_R4',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H4H5',
    'cad': 'Ring-H4H5',
})
M19061901_R5 = create_part({
    'name': 'M19061901_R5',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H5H6',
    'cad': 'Ring-H5H6',
})
M19061901_R6 = create_part({
    'name': 'M19061901_R6',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H6H7',
    'cad': 'Ring-H6H7',
})
M19061901_R7 = create_part({
    'name': 'M19061901_R7',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H7H8',
    'cad': 'Ring-H7H8',
})
M19061901_R8 = create_part({
    'name': 'M19061901_R8',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H8H9',
    'cad': 'Ring-H8H9',
})
M19061901_R9 = create_part({
    'name': 'M19061901_R9',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H9H10',
    'cad': 'Ring-H9H10',
})
M19061901_R10 = create_part({
    'name': 'M19061901_R10',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H10H11',
    'cad': 'Ring-H10H11',
})
M19061901_R11 = create_part({
    'name': 'M19061901_R11',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H11H12',
    'cad': 'Ring-H11H12',
})
M19061901_R12 = create_part({
    'name': 'M19061901_R12',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H12H13',
    'cad': 'Ring-H12H13',
})
M19061901_R13 = create_part({
    'name': 'M19061901_R13',
    'type': 'ring',
    'status': 'in_study',
    'material': MAT2_RING,
    'geometry': 'Ring-H13H14',
    'cad': 'Ring-H13H14',
})

M19061901_iL1 = create_part({
    'name': 'M19061901_iL1',
    'type': 'lead',
    'status': 'in_operation',
    'material': MAT_LEAD,
    'geometry': 'inner',
    'cad': 'Inner',
})
M19061901_oL2 = create_part({
    'name': 'M19061901_oL2',
    'type': 'lead',
    'status': 'in_operation',
    'material': MAT_LEAD,
    'geometry': 'outer-H14',
    'cad': 'Outer-H14',
})

MAT_TEST1 = create_material({
    'name': 'MAT_TEST1',
    'description': 'R1, R2',
    'nuance': 'Cu5Ag5,08',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 52.4e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 481,
})
MAT_TEST2 = create_material({
    'name': 'MAT_TEST2',
    'description': 'R1, R2',
    'nuance': 'Cu5Ag5,08',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 53.3e+6,
    'thermal_conductivity': 380,
    'magnet_permeability': 1,
    'young': 117e+9,
    'poisson': 0.33,
    'expansion_coefficient': 18e-6,
    'rpe': 482,
})

HLTESTH1 = create_part({
    'name': 'HL-34_H1',
    'type': 'helix',
    'design_office_reference': 'HL-34-001-A',
    'status': 'in_operation',
    'material': MAT_TEST1,
    'geometry': 'HL-31_H1',
    'cad': 'HL-31_H1',
})

HLTESTH2 = create_part({
    'name': 'HL-34_H2',
    'type': 'helix',
    'design_office_reference': 'HL-34-001-A',
    'status': 'in_operation',
    'material': MAT_TEST2,
    'geometry': 'HL-31_H2',
    'cad': 'HL-31_H2',
})
HLTESTR1 = create_part({
    'name': 'Ring-H1H2',
    'type': 'ring',
    'design_office_reference': 'HL-34-001-A',
    'status': 'in_operation',
    'material': MAT_TEST2,
    'geometry': 'Ring-H1H2',
    'cad': 'Ring-H1H2',
})

MTEST = create_site({
    'name': 'MTest',
    'status': 'in_study'
    # 'config': 'HL-test2-cfpdes-thelec-Axi-sim', # TODO MagConfile instead
})

MTest2 = create_site({
    'name': 'MTest2',
    'status': 'defunct',
})

HLtest = create_magnet({
    'name': 'HL-test',
    'status': 'in_study',
    'site': MTEST,
    'parts': [HLTESTH1, HLTESTH2, HLTESTR1],
    'geometry': 'test'
})

# Add tore for test
mattore = create_material({
'name': 'mtore',
    'nuance': 'test',
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

Tore = create_part({
'name':'tore',
    'type':'bitter',
    'geometry':'tore',
    'status': 'in_study',
    'material': mattore
})
m_MTore = create_site({
    'name': "MTore",
    'status': 'in_study'
})
MTore = create_magnet({
    'name': "Tore-test",
    'geometry':"MTore",
    'status': 'in_study',
    'site': m_MTore
})

M9_M19061901 = create_site({
    'name': 'M9_M19061901',
    'status': 'in_study'
    # 'config': 'MAGFILEM19061901.conf', # TODO MagConfile instead
})

M19061901 = create_magnet({
'name':"M19061901",
    'geometry': "HL-31",
    'status': 'in_study',
    'parts': [H15101601,
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
              M19061901_oL2],
    'site': M9_M19061901,
})

CUAG01 = create_material({
'name': 'CuAg01',
    'nuance': 'CuAg01',
    't_ref': 293,
    'volumic_mass': 9e+3,
    'specific_heat': 380,
    'alpha': 3.6e-3,
    'electrical_conductivity': 50.1e+6,
    'thermal_conductivity': 360,
    'magnet_permeability': 1,
    'young': 127e+9,
    'poisson': 0.335,
    'expansion_coefficient': 18e-6,
    'rpe': 481000000.0
})

M9BI = create_part({
'name': 'M9Bi',
    'type': 'bitter',
    'design_office_reference': 'BI-03-002-A',
    'status': 'in_study',
    'material': CUAG01,
    'geometry': 'M9_Bi',
})

M9BE = create_part({
'name': 'M9Be',
    'type': 'bitter',
    'design_office_reference': 'BE-03-002-A',
    'geometry': 'M9_Be',
    'status': 'in_study',
    'material': CUAG01
})

M9BITTERS = create_magnet({
'name': 'M9Bitters',
    'status': 'in_study',
    'parts': [M9BI, M9BE],
    'site': M9_M19061901,
    'geometry': 'M9Bitters',
    'design_office_reference': 'M9Bitters'
})

M10BI = create_part({
'name': 'M10Bi',
    'type': 'bitter',
    'design_office_reference': 'BI-03-002-A',
    'geometry': 'M10_Bi',
    'status': 'in_study',
    'material': CUAG01
})

M10BE = create_part({
'name': 'M10Be',
    'type': 'bitter',
    'design_office_reference': 'BE-03-002-A',
    'geometry': 'M10_Be',
    'status': 'in_study',
    'material': CUAG01
})

M10BITTERS = create_magnet({
'name': 'M10Bitters',
    'status': 'in_study',
    'parts': [M10BI, M10BE],
    'design_office_reference': 'M10Bitters'
})

CUAG008 = create_material({
    'name':"B_CuAg008",
    'nuance':"CuAg008",
    't_ref':293,
    'volumic_mass':9e+3,
    'specific_heat':380,
    'alpha':3.6e-3,
    'electrical_conductivity':50.1e+6,
    'thermal_conductivity':360,
    'magnet_permeability':1,
    'young':127e+9,
    'poisson':0.335,
    'expansion_coefficient':18e-6,
    'rpe':481000000.0
})

M8 = create_site({
    'name': 'M8',
    'status': 'in_study'
    # 'config': 'HL-test2-cfpdes-thelec-Axi-sim', # TODO MagConfile instead
})

M8BI = create_part({
'name': 'M8Bi',
    'type': 'bitter',
    'design_office_reference': 'BI-03-002-A',
    'geometry': 'M8Bitters_Bi',
    'status': 'in_study',
    'material': CUAG008
})

M8BE = create_part({
'name': 'M8Be',
    'type': 'bitter',
    'design_office_reference': 'BE-03-002-A',
    'geometry': 'M8Bitters_Be',
    'status': 'in_study',
    'material': CUAG008
})

M8BITTERS = create_magnet({
'name': 'M8Bitters',
    'status': 'in_study',
    'parts': [M8BI, M8BE],
    'design_office_reference': 'M8Bitters',
    'site':M8
})

LTS = create_material({
'name': 'LTS',
    'nuance': 'LTS',
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
    'rpe': 481000000.0,
})

HYBRID = create_part({
'name': 'Hybrid',
    'type': 'supra',
    'geometry':'Hybrid',
    'status':'in_study',
    'material':LTS
})

MHYBRID = create_magnet({
'name':"Hybrid",
    'status':'in_study',
    'parts': [HYBRID],
    'site':M8,
})
