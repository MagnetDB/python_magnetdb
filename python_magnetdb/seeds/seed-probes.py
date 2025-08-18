"""
Create probes
"""
from os import getenv

from .crud import create_probe, query_magnet
from ..models.probe import ProbeType

# Get parts from previous defs
HLtest = query_magnet('HLtest')

Vprobes = create_probe({
    'name':'tore',
    'probe_type': ProbeType.VOLTAGE,
    'index': ['U1', 'U2', 'U3'],
    'locatation': [[0,0,0], [0,0,1], [0,0,2]],
    'description': 'voltage probe per Helix with fakes coordinates',
    'magnet': HLtest
})
