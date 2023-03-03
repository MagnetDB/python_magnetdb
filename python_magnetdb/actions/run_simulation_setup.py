import json
import os
import subprocess
import tempfile
from argparse import Namespace
from os.path import basename
from traceback import print_exception

from python_magnetsetup.config import appenv
from python_magnetsetup.setup import setup

from python_magnetdb.actions.generate_magnet_directory import generate_magnet_directory
from python_magnetdb.actions.generate_site_directory import generate_site_directory
from python_magnetdb.models.attachment import Attachment


def prepare_directory(simulation, directory):
    if simulation.resource_type == 'magnets':
        return generate_magnet_directory(simulation.resource_id, directory)
    elif simulation.resource_type == 'sites':
        return generate_site_directory(simulation.resource_id, directory)
    raise Exception('Unsupported resource type')


def run_simulation_setup(simulation):
    simulation.setup_status = "in_progress"
    simulation.save()
    simulation.load('currents.magnet.parts')
    
    currents = {current.magnet.name: {'value': current.value, 'type': current.magnet.get_type() } for current in simulation.currents}
    print(f'currents={currents}')

    with tempfile.TemporaryDirectory() as tempdir:
        done = subprocess.run([f"rm -rf {tempdir}"], shell=True)
        done = subprocess.run([f"mkdir -p {tempdir}"], shell=True)

        print(f"generating config in {tempdir}...")
        prepare_directory(simulation, tempdir)
        # done = subprocess.run([f"ls -lR {tempdir}"], shell=True)
        print("generating config done")

        print(f"running setup... non_linear={simulation.non_linear} type={type(simulation.non_linear)}")
        data_dir = f"{tempdir}/data"
        current_dir = os.getcwd()
        os.chdir(tempdir)
        
        args = Namespace(wd=tempdir,
                         datafile=f"{tempdir}/config.json",
                         method=simulation.method,
                         time="static" if simulation.static else "transient",
                         geom=simulation.geometry,
                         model=simulation.model,
                         nonlinear=simulation.non_linear,
                         cooling=simulation.cooling,
                         flow_params=f"{tempdir}/flow_params.json",
                         debug=False,
                         verbose=False,
                         skip_archive=True)

        env = appenv(envfile=None, url_api=data_dir, yaml_repo=f"{data_dir}/geometries", cad_repo=f"{data_dir}/cad",
                     mesh_repo=data_dir, simage_repo=data_dir, mrecord_repo=data_dir, optim_repo=data_dir)
        try:
            with open(f"{tempdir}/config.json", "r") as config_file:
                config = json.load(config_file)
                (yamlfile, cfgfile, jsonfile, xaofile, meshfile) = setup(env, args, config, f"{tempdir}/{simulation.resource.name}", currents)
                simulation.setup_state = {
                    'yamlfile': yamlfile,
                    'cfgfile': cfgfile[len(tempdir) + 1:],
                    'jsonfile': jsonfile[len(tempdir) + 1:],
                    'xaofile': xaofile,
                    'meshfile': meshfile
                }
            # subprocess.run([f"pwd"], shell=True, check=True)
            # subprocess.run([f"ls -alrth"], shell=True, check=True)
            config_file_path = None
            for file in os.listdir(tempdir):
                if file.endswith('.cfg'):
                    config_file_path = f"{tempdir}/{file}"
                    break
            simulation_name = os.path.basename(os.path.splitext(config_file_path)[0])
            output_archive = f"{tempdir}/setup-{simulation_name}.tar.gz"
            print(f'Archiving setup files ({simulation.geometry})')
            if simulation.geometry == 'Axi':
                subprocess.run([f"tar --exclude=*.xao --exclude=*.brep -czf {output_archive} *"], shell=True, check=True)
            else:
                subprocess.run([f"tar czf {output_archive} *"], shell=True, check=True)
            attachment = Attachment.raw_upload(basename(output_archive), "application/x-tar", output_archive)
            simulation.setup_output_attachment().associate(attachment)
            simulation.setup_status = "done"
        except Exception as err:
            simulation.setup_status = "failed"
            print_exception(None, err, err.__traceback__)
        os.chdir(current_dir)
        simulation.save()
