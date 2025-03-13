from typing import TextIO
from typing import Type

from ..models import StorageAttachment
from ..models.server import Server
from ..models.simulation import Simulation


import os
import tempfile
from argparse import Namespace
from os.path import basename
from traceback import print_exception

from fabric import Connection
from python_magnetsetup.config import appenv
from python_magnetsetup.job import JobManager, JobManagerType
from python_magnetsetup.node import NodeSpec, NodeType
from python_magnetsetup.setup import setup_cmds


def run_cmd(connection: Connection, cmd: str, stdout: TextIO):
    print(f'run_cmd: cmd={cmd}')
    stdout.write(f"=== RUNNING CMD: {cmd}\n")
    res = connection.run(cmd)
    stdout.write(f"===\n")
    stdout.write(res.stdout)
    if len(res.stderr) > 0:
        stdout.write(f"=== STDERR:\n")
        stdout.write(f"===\n")
        stdout.write(res.stderr)
    stdout.write(f"=== STATUS CODE: {res.exited}\n")
    stdout.flush()
    return res.stdout


def run_ssh_simulation(simulation: Simulation, server: Server, cores):
    simulation.status = "in_progress"
    simulation.save()

    currents = {current.magnet.name: {'value': current.value, 'type': current.magnet.type } for current in simulation.simulationcurrent_set.all()}
    print(f'currents={currents}')

    with tempfile.TemporaryDirectory() as local_tempdir:
        current_dir = os.getcwd()
        os.chdir(local_tempdir)
        log_file_path = f"{local_tempdir}/debug.log"
        with open(log_file_path, "a") as log_file:
            try:
                # TODO try to use native ssh key for API
                try:
                    ssh_key = f"{local_tempdir}/ssh_key"
                    with open(ssh_key, "w") as f:
                        f.write(server.private_key)
                    connection = Connection(host=server.host, user=server.username, connect_kwargs={'key_filename': ssh_key})
                except:
                    print(f'Failed to connect to {server.host} with magnetdb private ssh key')
                    print(f'Trying to connect with {server.username} native ssh key')
                    connection = Connection(host=server.host, user=server.username)

                log_file.write("Downloading setup archive...\n")
                simulation.setup_output_attachment.download(f"{local_tempdir}/setup.tar.gz")
                remote_temp_dir = run_cmd(connection, 'mktemp -d', log_file).strip()
                print(f'remote_temp_dir={remote_temp_dir} (type={type(remote_temp_dir)})')
                connection.put(f"{local_tempdir}/setup.tar.gz", remote_temp_dir)
                log_file.write("Extracting setup archive...\n")
                run_cmd(connection, f"tar xf {remote_temp_dir}/setup.tar.gz -C {remote_temp_dir}", log_file)
                log_file.write("Generating commands...\n")
                data_dir = f"{remote_temp_dir}/data"
                print(f'data_dir={data_dir}')
                args = Namespace(wd=remote_temp_dir,
                                 datafile=f"{remote_temp_dir}/config.json",
                                 method=simulation.method,
                                 time="static" if simulation.static else "transient",
                                 geom=simulation.geometry,
                                 model=simulation.model,
                                 nonlinear=simulation.non_linear,
                                 cooling=simulation.cooling,
                                 flow_params=f"{remote_temp_dir}/flow_params.json",
                                 np=cores,
                                 debug=False,
                                 verbose=False,
                                 skip_archive=True)
                # check yaml_repo, cad_repo - are they really used??
                env = appenv(envfile=None, url_api=data_dir, yaml_repo=f"{remote_temp_dir}/geometries",
                             cad_repo=f"{remote_temp_dir}/cad", mesh_repo=data_dir, simage_repo=server.image_directory,
                             mrecord_repo=data_dir, optim_repo=data_dir)
                node_spec = NodeSpec(name=server.name, otype=server.type, smp=server.smp, dns=server.host,
                                     cores=server.cores, multithreading=server.multithreading,
                                     manager=JobManager(otype=server.job_manager, queues=[]),
                                     mgkeydir=server.mesh_gems_directory)
                cmds = setup_cmds(env, args, node_spec, simulation.setup_state['yamlfile'],
                                  simulation.setup_state['cfgfile'], simulation.setup_state['jsonfile'],
                                  simulation.setup_state['xaofile'], simulation.setup_state['meshfile'],
                                  remote_temp_dir, currents)

                # Save cmds in a file
                print('Commands to be run:')
                with open("cmds.txt", "a") as f:
                    log_file.write(f"Saving commands... pwd({os.getcwd()}) \n")
                    for (key, value) in cmds.items():
                        f.write(f'{key}: {value}')
                        print(f'{key}: {value}')

                # geom_dir = f'{remote_temp_dir}/data/geometries'
                geom_dir = os.path.join(remote_temp_dir, 'data', 'geometries')
                with connection.cd(geom_dir):
                    log_file.write(f"Performing CAD...\n")
                    run_cmd(connection, cmds['CAD'], log_file)

                with connection.cd(remote_temp_dir):
                    for (key, value) in cmds.items():
                        # TODO ignore Run only if model is not including elasticity
                        # otherwise ignore Workflow
                        if key in ['Unpack', 'CAD', 'Run']:
                            continue
                        log_file.write(f"Performing {key}...\n")
                        print(f'Running {key}: {value}')
                        if key in ['Update_cfg', 'Update_Mesh']:
                            run_cmd(connection, value, log_file)
                        else:
                            run_cmd(connection, f"bash -c '{value}'", log_file)

                    log_file.write("Archiving results...\n")
                    simulation_name = os.path.basename(os.path.splitext(simulation.setup_state['cfgfile'])[0])
                    remote_output_archive = f"{remote_temp_dir}/{simulation_name}.tar.gz"
                    run_cmd(connection, f"tar --exclude=tmp.hdf --exclude=setup.tar.gz -czf {remote_output_archive} *", log_file)
                    local_output_archive = f"{local_tempdir}/{simulation_name}.tar.gz"
                    connection.get(remote_output_archive, local_output_archive)
                    simulation.output_attachment = StorageAttachment.raw_upload(basename(local_output_archive), "application/x-tar", local_output_archive)

                log_file.write("Done!\n")
                simulation.status = "done"
            except Exception as err:
                log_file.flush()
                simulation.status = "failed"
                print_exception(None, err, err.__traceback__)

            simulation.log_attachment = StorageAttachment.raw_upload("debug.log", "text/plain", log_file_path)
            os.chdir(current_dir)
            simulation.save()
