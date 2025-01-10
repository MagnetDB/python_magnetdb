import json
import os

from python_magnetdb.utils.yaml_json import yaml_to_json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_magnetdb.settings')

import django
django.setup()

import re
from datetime import datetime
from os import path, getenv

from python_magnetdb.models import StorageAttachment
from python_magnetdb.models.magnet import Magnet
from python_magnetdb.models.material import Material
from python_magnetdb.models.part import Part
from python_magnetdb.models.record import Record
from python_magnetdb.models.site import Site

data_directory = getenv('DATA_DIR')


def upload_attachment(file: str) -> StorageAttachment:
    try:
        return StorageAttachment.raw_upload(path.basename(file), 'text/tsv', file)
    except Exception as e:
        print("failed to upload attachment: {}".format(e))
        return None


def create_material(obj):
    """create material"""
    return Material.objects.create(**obj)


def create_part(obj):
    """create part"""
    print("creating part {}".format(obj['name']))
    geometry = obj.pop('geometry', None)
    cad = obj.pop('cad', None)
    part = Part(**obj)
    if geometry is not None:
        with open(path.join(data_directory, 'geometries', f"{geometry}.yaml")) as file:
            part.geometry_config = json.loads(yaml_to_json(file.read()))
    part.save()
    if cad is not None:
        for file in [f"{cad}.xao", f"{cad}.brep"]:
            attachment = upload_attachment(path.join(data_directory, 'cad', file))
            if attachment is not None:
                part.cadattachment_set.create(part=part, attachment=attachment)
    return part


def create_site(obj):
    """create site"""
    config = obj.pop('config', None)
    site = Site(**obj)
    if config is not None:
        attachment = upload_attachment(path.join(data_directory, 'conf', f"{config}"))
        if attachment is not None:
            site.config_attachment = attachment
    site.save()
    return site


def create_magnet(obj):
    """create magnet"""
    site = obj.pop('site', None)
    parts = obj.pop('parts', None)
    geometry = obj.pop('geometry', None)
    cad = obj.pop('cad', None)
    magnet = Magnet(**obj)
    if geometry is not None:
        attachment = upload_attachment(path.join(data_directory, 'geometries', f"{geometry}.yaml"))
        if attachment is not None:
            magnet.geometry_attachment = attachment
    magnet.save()
    if cad is not None:
        for file in [f"{cad}.xao", f"{cad}.brep"]:
            attachment = upload_attachment(path.join(data_directory, 'cad', file))
            if attachment is not None:
                magnet.cadattachment_set.create(magnet=magnet, attachment=attachment)
    if site is not None:
        magnet.sitemagnet_set.create(site=site, commissioned_at=datetime.now())
    if parts is not None:
        for part in parts:
            print('part:', part.name)
            magnet.magnetpart_set.create(commissioned_at=datetime.now(), part=part)
    return magnet


def extract_date_from_filename(filename):
    for match in re.finditer(r".+_(\d{4}).(\d{2}).(\d{2})---(\d{2}):(\d{2}):(\d{2}).+", filename):
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)),
                        int(match.group(4)), int(match.group(5)), int(match.group(6)))
    return None


def create_record(obj):
    """create a record from file for site"""

    file = obj.pop('file', None)
    site = obj.pop('site', None)
    if file is not None and site is not None:
        print(f'{data_directory}/mrecords/{file}')
        print(f"{path.basename(path.join(data_directory, 'mrecords', file))}")
        created_at = extract_date_from_filename(path.basename(path.join(data_directory, 'mrecords', file)))
        print(f'created_at={created_at}')
        if created_at is None:
            created_at = datetime.now()

        attachment = upload_attachment(path.join(data_directory, 'mrecords', file))
        if attachment is None:
            return None

        return Record.objects.create(
            name=path.basename(path.join(data_directory, 'mrecords', file)),
            created_at=created_at,
            attachment=attachment,
            site=site,
        )


def query_by_name(model_class, name: str):
    """
    Generic function to search a model object by name

    Args:
        model_class: The Django model class (e.g., Material, Site)
        name (str): Name to search for
    """
    try:
        return model_class.objects.get(name=name)
    except model_class.DoesNotExist:
        print(f'{model_class.__name__}[name={name}] no such object')
        return None
    except model_class.MultipleObjectsReturned:
        raise Exception(f'{model_class.__name__}[name={name}] returns more than one object')


def query_part(name: str):
    """search a part object by name"""
    return query_by_name(Part, name)


def query_material(name: str):
    """search a material object by name"""
    return query_by_name(Material, name)


def query_site(name: str):
    """search a site object by name"""
    return query_by_name(Site, name)
