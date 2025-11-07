"""
Create probes
"""
from os import getenv

from .crud import create_probe, query_magnet, query_probes
from ..models.probe import ProbeType

# Get parts from previous defs
HLtest = query_magnet('HL-test')
Vprobes = query_probes('HLtest-probes')
if Vprobes is not None:
    print("HLtest-probes already exists, skipping creation")
else:
    print("Creating HLtest-probes")
    Vprobes = create_probe({
        'name':'HLtest-probes',
        'type': ProbeType.VOLTAGE,
        'labels': ['U1', 'U2', 'U3'],
        'points': [[0,0,0], [0,0,1], [0,0,2]],
        'description': 'voltage probe per Helix with fakes coordinates',
        'magnet': HLtest
    })
