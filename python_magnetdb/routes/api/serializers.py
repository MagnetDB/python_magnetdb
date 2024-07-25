from django.db import models
from django.db.models import DateTimeField
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor

from python_magnetdb.models import Site


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
    return res


POST_PROCESSORS = {
    Site: _site_post_processor,
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

