import json
from typing import List

from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from fastapi import APIRouter, Query, HTTPException, Depends, UploadFile
from fastapi import Response
from fastapi.params import Form, File

from .serializers import model_serializer
from ...dependencies import get_user
from ...models import Part, Material, AuditLog, StorageAttachment
from ...models.part import PartType
from ...utils.yaml_json import yaml_to_json

router = APIRouter()


@router.get("/api/parts")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query("created_at"), sort_desc: bool = Query(False),
          status: List[str] = Query(default=None, alias="status[]"),
          type: List[str] = Query(default=None, alias="type[]")):
    db_query = Part.objects
    if status is not None and len(status) > 0:
        db_query = db_query.filter(status__in=status)
    if type is not None and len(type) > 0:
        db_query = db_query.filter(type__in=type)
    if query is not None and query.strip() != '':
        db_query = db_query.filter(Q(name__icontains=query))
    if sort_by is not None:
        order_field = f"-{sort_by}" if sort_desc else sort_by
        db_query = db_query.order_by(order_field)
    paginator = Paginator(db_query.all(), per_page)
    items = [model_serializer(site) for site in paginator.get_page(page).object_list]
    return {
        "current_page": page,
        "last_page": paginator.num_pages,
        "total": paginator.count,
        "items": items,
    }


@router.post("/api/parts")
def create(
    user=Depends(get_user('create')), name: str = Form(...), description: str = Form(None),
    type: PartType = Form(...), material_id: str = Form(...), design_office_reference: str = Form(None),
    metadata: str = Form('{}'),
):
    material = Material.objects.filter(id=material_id).get()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    part = Part(
        name=name,
        description=description,
        status='in_study',
        type=type,
        design_office_reference=design_office_reference,
        material=material,
        metadata=json.loads(metadata),
    )
    try:
        part.save()
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail="Name already taken.") if 'parts_name_unique' in str(e) else e
    AuditLog.log(user, "Part created", resource=part)
    return model_serializer(part)


@router.get("/api/parts/{id}/sites")
def sites(id: int, user=Depends(get_user('read'))):
    part = Part.objects \
        .prefetch_related('magnetpart_set__magnet__sitemagnet_set__site') \
        .get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    result = []
    for magnet_part in part.magnetpart_set.all():
        for site_magnet in magnet_part.magnet.sitemagnet_set.all():
            result.append(model_serializer(site_magnet.site))
    return {'sites': result}


@router.get("/api/parts/{id}/records")
def records(id: int, user=Depends(get_user('read'))):
    part = Part.objects \
        .prefetch_related('magnetpart_set__magnet__sitemagnet_set__site__record_set') \
        .get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    result = []
    for magnet_part in part.magnetpart_set.all():
        for site_magnet in magnet_part.magnet.sitemagnet_set.all():
            for record in site_magnet.site.record_set.all():
                result.append(model_serializer(record))
    return {'records': result}


@router.get("/api/parts/{id}")
def show(id: int, user=Depends(get_user('read'))):
    part = Part.objects\
        .select_related('material', 'hts_attachment', 'shape_attachment')\
        .prefetch_related('cadattachment_set__attachment', 'magnetpart_set__magnet')\
        .get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    return model_serializer(part)


@router.patch("/api/parts/{id}")
def update(
    id: int, user=Depends(get_user('update')), name: str = Form(...), description: str = Form(None),
    type: PartType = Form(...), material_id: str = Form(...), design_office_reference: str = Form(None),
    geometry_yaml_config: str = Form(None), geometry_hts: UploadFile = File(None),
    geometry_shape: UploadFile = File(None), metadata: str = Form(None),
):
    part = Part.objects \
        .select_related('material', 'hts_attachment', 'shape_attachment') \
        .prefetch_related('cadattachment_set__attachment', 'magnetpart_set__magnet') \
        .get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    material = Material.objects.filter(id=material_id).get()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    part.name = name
    part.description = description
    part.type = type
    part.design_office_reference = design_office_reference
    part.material = material
    if geometry_yaml_config is not None:
        part.geometry_config = json.loads(yaml_to_json(geometry_yaml_config))
    if geometry_hts is not None and part.allow_hts_file:
        part.hts_attachment = StorageAttachment.upload(geometry_hts)
    if geometry_shape is not None and part.allow_shape_file:
        part.shape_attachment = StorageAttachment.upload(geometry_shape)
    if metadata is not None:
        part.metadata = json.loads(metadata)
    part.save()
    AuditLog.log(user, "Part updated", resource=part)
    return model_serializer(part)


@router.get("/api/parts/{id}/geometry.yaml")
def geometry(id: int, user=Depends(get_user('read'))):
    part = Part.objects.get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    return Response(content=part.geometry_config_to_yaml, media_type="application/x-yaml")


@router.post("/api/parts/{id}/defunct")
def defunct(id: int, user=Depends(get_user('update'))):
    part = Part.objects.get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    part.status = 'defunct'
    part.save()
    AuditLog.log(user, "Part defunct", resource=part)
    return model_serializer(part)


@router.delete("/api/parts/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    part = Part.objects.get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    part.delete()
    AuditLog.log(user, "Part deleted", resource=part)
    return model_serializer(part)
