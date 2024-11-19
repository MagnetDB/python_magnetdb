import os
import subprocess
import tempfile
from os.path import join, isfile

from pandas import read_csv

from python_magnetdb.models import Simulation


def find_measures_files(path: str):
    found_files = []
    for file in os.listdir(path):
        file_path = join(path, file)
        if isfile(file_path):
            continue
        if file.endswith('.measures'):
            found_files.append(file_path)
            continue
        found_files = found_files + find_measures_files(file_path)
    return found_files


def get_simulation_measures(simulation_id: int, measure_name: str=None):
    print(f"get_simulation_measures... simulation_id:{simulation_id}, measure:{measure_name}")
    simulation = Simulation.objects.prefetch_related('output_attachment').get(id=simulation_id)
    if simulation.output_attachment is None:
        return None

    with tempfile.TemporaryDirectory() as tempdir:
        # Can we rename output.tar.gz to  a more significant filename like in run_simulation_setup.py (aka simulation_name L83) ?
        simulation.output_attachment.download(f"{tempdir}/output.tar.gz")
        subprocess.run([f"tar xf {tempdir}/output.tar.gz -C {tempdir}"], shell=True, check=True)

        measures_files = find_measures_files(tempdir)
        measures_names = list(map(lambda file: file.split('/').pop()[:-9], measures_files))

        for (index, measures_path) in enumerate(measures_files):
            if measure_name is None or measures_path.endswith(f"{measure_name}.measures"):
                csv = read_csv(f"{measures_path}/values.csv")
                return {
                    'measure': measures_path.split('/').pop()[:-9],
                    'available_measures': measures_names,
                    'columns': csv.columns.tolist(),
                    'rows': csv.values.tolist(),
                }
    return None
