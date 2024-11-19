import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_magnetdb.settings')

import django
django.setup()

from celery import Celery
from python_magnetdb.models import Simulation, Server

app = Celery('tasks', broker=os.getenv('REDIS_ADDR') or 'redis://localhost:6379/0')


@app.task
def run_simulation(simulation_id, server_id, cores):
    from .actions.run_simulation import run_simulation
    from .actions.run_ssh_simulation import run_ssh_simulation
    if server_id is not None:
        return run_ssh_simulation(Simulation.objects.get(id=simulation_id), Server.objects.get(id=server_id), cores)
    else:
        return run_simulation(Simulation.objects.get(id=simulation_id))


@app.task
def run_simulation_setup(simulation_id):
    from .actions.run_simulation_setup import run_simulation_setup
    return run_simulation_setup(Simulation.objects.get(id=simulation_id))
