import tempfile

from python_magnetdb.actions.generate_simulation_config import generate_site_config

from python_magnetdb.models.site import Site
from python_magnetsetup.ana import magnet_setup, msite_setup
from python_magnetsetup.config import appenv

from python_magnetdb.actions.generate_magnet_directory import generate_magnet_directory


def get_magnet_data(magnet_id):
    with tempfile.TemporaryDirectory() as tempdir:
        config_data = generate_magnet_directory(magnet_id, tempdir)
        data_dir = f"{tempdir}/data"
        env = appenv(envfile=None, url_api=data_dir, yaml_repo=f"{data_dir}/geometries", cad_repo=f"{data_dir}/cad",
                     mesh_repo=data_dir, simage_repo=data_dir, mrecord_repo=data_dir, optim_repo=data_dir)
        return magnet_setup(env, config_data, True)


def get_site_data(site_id):
    site = Site.with_('site_magnets').find(site_id)
    with tempfile.TemporaryDirectory() as tempdir:
        for site_magnet in site.site_magnets:
            if not site_magnet.active:
                continue
            generate_magnet_directory(site_magnet.magnet_id, tempdir)
        data_dir = f"{tempdir}/data"
        env = appenv(envfile=None, url_api=data_dir, yaml_repo=f"{data_dir}/geometries", cad_repo=f"{data_dir}/cad",
                     mesh_repo=data_dir, simage_repo=data_dir, mrecord_repo=data_dir, optim_repo=data_dir)
        config_data = generate_site_config(site_id)
        return msite_setup(env, config_data, True)
