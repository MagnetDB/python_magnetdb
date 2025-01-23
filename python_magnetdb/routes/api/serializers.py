from django.db import models
from django.db.models import DateTimeField
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor

from python_magnetdb.models import Site, Material, Part, Magnet, Simulation
from python_magnetdb.models.magnet import MagnetType


def _site_post_processor(model: Site, res: dict):
    site_magnets = model.sitemagnet_set.all()
    res['commissioned_at'] = sorted(
        list(map(lambda curr: curr.commissioned_at, site_magnets)), reverse=True
    )[0].isoformat() if len(site_magnets) > 0 else None
    decommissioned_at = list(
        filter(lambda curr: curr is not None, map(lambda curr: curr.decommissioned_at, list(site_magnets)))
    )
    res['decommissioned_at'] = sorted(decommissioned_at, reverse=True)[0].isoformat() if len(decommissioned_at) > 0 else None
    if 'sitemagnet_set' in res:
        res['site_magnets'] = res['sitemagnet_set']
        del res['sitemagnet_set']
    if 'config_attachment' in res:
        res['config'] = res['config_attachment']
        del res['config_attachment']
    return res


def _material_post_processor(model: Material, res: dict):
    if 'part_set' in res:
        res['parts'] = res['part_set']
        del res['part_set']
    return res


def _part_post_processor(model: Part, res: dict):
    if 'magnetpart_set' in res:
        res['magnet_parts'] = res['magnetpart_set']
        del res['magnetpart_set']
    if 'cadattachment_set' in res:
        res['cad'] = res['cadattachment_set']
        del res['cadattachment_set']
    if 'hts_attachment' in res:
        res['hts'] = res['hts_attachment']
        del res['hts_attachment']
    if 'shape_attachment' in res:
        res['shape'] = res['shape_attachment']
        del res['shape_attachment']
    res['allow_hts_file'] = model.allow_hts_file
    res['allow_shape_file'] = model.allow_shape_file
    return res


def _magnet_post_processor(model: Magnet, res: dict):
    commissioned_at = None
    decommissioned_at = None
    if 'sitemagnet_set' in res:
        site_magnet = sorted(
            res['sitemagnet_set'],
            key=lambda site_magnet: site_magnet['commissioned_at'],
            reverse=True
        )[0]
        if site_magnet is not None:
            commissioned_at = site_magnet['commissioned_at']
            decommissioned_at = site_magnet['decommissioned_at']
        res['site_magnets'] = res['sitemagnet_set']
        del res['sitemagnet_set']
    res['supported_part_types'] = MagnetType(model.type).supported_part_types
    res['commissioned_at'] = commissioned_at
    res['decommissioned_at'] = decommissioned_at

    if 'magnetpart_set' in res:
        res['magnet_parts'] = res['magnetpart_set']
        del res['magnetpart_set']

    if 'geometry_attachment' in res:
        res['geometry'] = res['geometry_attachment']
        del res['geometry_attachment']

    if 'cadattachment_set' in res:
        res['cad'] = res['cadattachment_set']
        del res['cadattachment_set']
    return res


def _simulation_post_processor(model: Simulation, res: dict):
    if 'simulationcurrent_set' in res:
        res['currents'] = res['simulationcurrent_set']
        del res['simulationcurrent_set']
    if 'owner' in res:
        res["owner"] = {"name": res["owner"]["name"]}
    if model.resource is not None:
        res["resource_type"] = model.resource_type
        res["resource_id"] = model.resource_id
        res["resource"] = model_serializer(model.resource)
    return res


POST_PROCESSORS = {
    Site: _site_post_processor,
    Material: _material_post_processor,
    Part: _part_post_processor,
    Magnet: _magnet_post_processor,
    Simulation: _simulation_post_processor,
}


def model_serializer(model: models.Model, already_processed = []):
    res = {}
    for field in model._meta.fields:
        if not isinstance(field, ForeignKey):
            res[field.name] = getattr(model, field.name)
            if isinstance(field, DateTimeField) and res[field.name] is not None:
                res[field.name] = res[field.name].isoformat()
        elif field.name in model._state.fields_cache:
            value = getattr(model, field.name)
            if value is not None and value not in already_processed:
                res[field.name] = model_serializer(value, already_processed + [model])
            else:
                res[field.name] = None
    if hasattr(model, '_prefetched_objects_cache'):
        for attr_name in model._prefetched_objects_cache:
            attr = getattr(model.__class__, attr_name)
            if isinstance(attr, ReverseManyToOneDescriptor):
                values = list(filter(
                    lambda value: value not in already_processed,
                    model._prefetched_objects_cache[attr_name]
                ))
                if len(values) > 0:
                    res[attr_name] = [model_serializer(value, already_processed + [model]) for value in values]
    if model.__class__ in POST_PROCESSORS:
        POST_PROCESSORS[model.__class__](model, res)
    return res

