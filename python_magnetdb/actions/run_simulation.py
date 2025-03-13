import os
import subprocess
import tempfile
from argparse import Namespace
from os.path import basename
from traceback import print_exception

from python_magnetsetup.config import appenv
from python_magnetsetup.job import JobManager, JobManagerType
from python_magnetsetup.node import NodeSpec, NodeType

from python_magnetdb.models import StorageAttachment, Simulation
from python_magnetsetup.setup import setup_cmds


def run_cmd(cmd, stdout):
    res = subprocess.run(cmd, shell=True, capture_output=True)
    stdout.write(f"=== RUNNING CMD: {' '.join(cmd)}\n")
    stdout.write(f"===\n")
    stdout.write(res.stdout.decode("utf-8"))
    if len(res.stderr) > 0:
        stdout.write(f"=== STDERR:\n")
        stdout.write(f"===\n")
        stdout.write(res.stderr.decode("utf-8"))
    stdout.write(f"=== STATUS CODE: {res.returncode}\n")


def run_simulation(simulation: Simulation):
    simulation.status = "in_progress"
    simulation.save()
    currents = {current.magnet.name: current.value for current in simulation.simulationcurrent_set.all()}

    with tempfile.TemporaryDirectory() as tempdir:
        current_dir = os.getcwd()
        os.chdir(tempdir)
        log_file_path = f"{tempdir}/debug.log"
        with open(log_file_path, "a") as log_file:
            try:
                log_file.write("Downloading setup archive...\n")
                simulation.setup_output_attachment.download(f"{tempdir}/setup.tar.gz")
                log_file.write("Extracting setup archive...\n")
                run_cmd([f"tar xvf {tempdir}/setup.tar.gz -C {tempdir}"], log_file)
                log_file.write("Generating commands...\n")
                data_dir = f"{tempdir}/data"
                args = Namespace(wd=tempdir,
                                 datafile=f"{tempdir}/config.json",
                                 method=simulation.method,
                                 time="static" if simulation.static else "transient",
                                 geom=simulation.geometry,
                                 model=simulation.model,
                                 nonlinear=simulation.non_linear,
                                 cooling=simulation.cooling,
                                 flow_params=f"{tempdir}/flow_params.json",
                                 machine='unknown',
                                 np=0,
                                 debug=False,
                                 verbose=False,
                                 skip_archive=True)
                env = appenv(envfile=None, url_api=data_dir, yaml_repo=f"{data_dir}/geometries",
                             cad_repo=f"{data_dir}/cad", mesh_repo=data_dir, simage_repo=os.getenv('IMAGES_DIR'),
                             mrecord_repo=data_dir, optim_repo=data_dir)
                node_spec = NodeSpec(name="local-node", otype=NodeType.compute, smp=True, dns=server.host, cores=8,
                                     multithreading=True, manager=JobManager(otype=JobManagerType.none, queues=[]),
                                     mgkeydir=None)
                cmds = setup_cmds(env, args, node_spec, simulation.setup_state['yamlfile'],
                                  simulation.setup_state['cfgfile'],
                                  simulation.setup_state['jsonfile'],
                                  simulation.setup_state['xaofile'],
                                  simulation.setup_state['meshfile'],
                                  simulation.setup_state['csvfiles'],
                                  tempdir,
                                  currents)

                # Save cmds in a file
                with open("cmds.txt", "a") as f:
                    log_file.write("Saving commands...\n")
                    for (key, value) in cmds.items():
                        f.write(f'{key}: {value}')

                # Save cmds in a file
                with open("cmds.txt", "a") as f:
                    log_file.write("Saving commands...\n")
                    for (key, value) in cmds.items():
                        f.write(f'{key}: {value}')

                for (key, value) in cmds.items():
                    if key in ['Unpack', 'Workflow']:
                        continue
                    if key in ['Update_cfg', 'Update_Mesh']:
                        log_file.write(f"{value}\n")
                        run_cmd([value], log_file)
                    else:
                        run_cmd([f"bash -c \"{value}\""], log_file)

                log_file.write("Archiving results...\n")
                simulation_name = os.path.basename(os.path.splitext(simulation.setup_state['cfgfile'])[0])
                output_archive = f"{tempdir}/{simulation_name}.tar.gz"
                run_cmd([f"tar --exclude=tmp.hdf --exclude=setup.tar.gz -cvzf {output_archive} *"], log_file)
                simulation.output_attachment = StorageAttachment.raw_upload(basename(output_archive), "application/x-tar", output_archive)
                log_file.write("Done!\n")
                simulation.status = "done"
            except Exception as err:
                simulation.status = "failed"
                print_exception(None, err, err.__traceback__)
            simulation.log_attachment = StorageAttachment.raw_upload("debug.log", "text/plain", log_file_path)
            os.chdir(current_dir)
            simulation.save()
