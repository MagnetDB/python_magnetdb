import json
import os
import shutil

from python_magnetdb.actions.generate_simulation_config import generate_magnet_config
from python_magnetdb.models.magnet import Magnet


def mkdir(dir):
    try:
        os.mkdir(dir)
    except FileExistsError:
        pass


def generate_magnet_directory(magnet_id, directory):
    magnet = Magnet.objects.prefetch_related(
        "magnetpart_set__part__partgeometry_set__attachment",
        "magnetpart_set__part__cadattachment_set__attachment",
        "geometry_attachment",
        "magnetpart_set__part__material",
        "sitemagnet_set__site",
        "cadattachment_set__attachment",
    ).get(id=magnet_id)
    mkdir(f"{directory}/data")
    mkdir(f"{directory}/data/geometries")
    mkdir(f"{directory}/data/cad")
    print(f"generate_magnet_directory: {os.getcwd()}/flow_params.json")
    shutil.copyfile(f"{os.getcwd()}/flow_params.json", f"{directory}/flow_params.json")
    if magnet.geometry_attachment:
        magnet.geometry_attachment.download(
            f"{directory}/data/geometries/{magnet.geometry_attachment.filename}"
        )
    for magnet_part in magnet.magnetpart_set.all():
        # if not magnet_part.active:
        #     continue
        for geometry in magnet_part.part.partgeometry_set.all():
            geometry.attachment.download(
                f"{directory}/data/geometries/{geometry.attachment.filename}"
            )
        if magnet_part.part.cadattachment_set.all():
            for cad in magnet_part.part.cadattachment_set.all():
                cad.attachment.download(
                    f"{directory}/data/cad/{cad.attachment.filename}"
                )
    with open(f"{directory}/config.json", "w+") as file:
        config = generate_magnet_config(magnet_id)
        file.write(json.dumps(config))
        return config
