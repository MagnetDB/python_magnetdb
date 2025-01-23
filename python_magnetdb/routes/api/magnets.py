from datetime import datetime
from typing import List

from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from fastapi import APIRouter, Query, HTTPException, Form, Depends, Response

from .serializers import model_serializer
from ...actions.generate_magnet_directory import generate_magnet_directory
from ...dependencies import get_user
from ...models import Magnet, AuditLog
from ...models.magnet import MagnetType
from ...models.status import Status

router = APIRouter()


@router.get("/api/magnets")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query('created_at'), sort_desc: bool = Query(False),
          status: List[str] = Query(default=None, alias="status[]")):
    db_query = Magnet.objects.prefetch_related('sitemagnet_set')
    if query is not None and query.strip() != '':
        db_query = db_query.filter(Q(name__icontains=query))
    if status is not None:
        db_query = db_query.filter(Q(status__in=status))
    if sort_by is not None:
        order_field = f"-{sort_by}" if sort_desc else sort_by
        db_query = db_query.order_by(order_field)
    paginator = Paginator(db_query.all(), per_page)
    items = [model_serializer(magnet) for magnet in paginator.get_page(page).object_list]
    return {
        "current_page": page,
        "last_page": paginator.num_pages,
        "total": paginator.count,
        "items": items,
    }


@router.post("/api/magnets")
def create(
    user=Depends(get_user("create")),
    name: str = Form(...),
    type: MagnetType = Form(...),
    description: str = Form(None),
    design_office_reference: str = Form(None),
):
    magnet = Magnet(
        name=name,
        type=type,
        description=description,
        design_office_reference=design_office_reference,
        status=Status.IN_STUDY,
    )
    try:
        magnet.save()
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail="Name already taken.") if 'magnets_name_unique' in str(e) else e
    AuditLog.log(user, "Magnet created", resource=magnet)
    return model_serializer(magnet)


@router.get("/api/magnets/{id}/sites")
def sites(id: int, user=Depends(get_user("read"))):
    magnet = Magnet.objects.prefetch_related('sitemagnet_set__site').get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    result = []
    for site_magnet in magnet.sitemagnet_set.all():
        result.append(model_serializer(site_magnet))
    return {"sites": result}


@router.get("/api/magnets/{id}/geometry.yaml")
def geometry(id: int, user=Depends(get_user('read'))):
    magnet = Magnet.objects.get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    return Response(content=magnet.geometry_config_to_yaml, media_type="application/x-yaml")


@router.get("/api/magnets/{id}/records")
def records(id: int, user=Depends(get_user("read"))):
    magnet = Magnet.objects.prefetch_related('sitemagnet_set__site__record_set').get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    result = []
    for site_magnet in magnet.sitemagnet_set.all():
        for record in site_magnet.site.record_set.all():
            result.append(model_serializer(record))
    return {"records": result}


@router.get("/api/magnets/{id}/mdata")
def mdata(id: int, user=Depends(get_user("read"))):
    magnet = Magnet.objects.get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    data = generate_magnet_directory(id)
    return {"results": data}


@router.get("/api/magnets/{id}")
def show(id: int, user=Depends(get_user("read"))):
    magnet = Magnet.objects\
        .prefetch_related('magnetpart_set__part', 'sitemagnet_set__site', 'cadattachment_set__attachment')\
        .get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    return model_serializer(magnet)


@router.patch("/api/magnets/{id}")
def update(
    id: int,
    user=Depends(get_user("update")),
    name: str = Form(...),
    description: str = Form(None),
    design_office_reference: str = Form(None),
    inner_bore: float = Form(None),
    outer_bore: float = Form(None),
):
    magnet = Magnet.objects \
        .prefetch_related('magnetpart_set__part', 'sitemagnet_set__site', 'cadattachment_set__attachment') \
        .get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    magnet.name = name
    magnet.description = description
    magnet.design_office_reference = design_office_reference
    magnet.inner_bore = inner_bore
    magnet.outer_bore = outer_bore
    magnet.save()
    AuditLog.log(user, "Magnet updated", resource=magnet)
    return model_serializer(magnet)


@router.post("/api/magnets/{id}/defunct")
def defunct(id: int, decommissioned_at: datetime = Form(datetime.now()), user=Depends(get_user('update'))):
    magnet = Magnet.objects \
        .prefetch_related('magnetpart_set__part', 'sitemagnet_set__site', 'cadattachment_set__attachment') \
        .get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    for magnet_part in magnet.magnetpart_set.all():
        if not magnet_part.active:
            continue
        magnet_part.part.status = Status.IN_STOCK
        magnet_part.part.save()
        magnet_part.decommissioned_at = decommissioned_at
        magnet_part.save()

    magnet.status = Status.DEFUNCT
    magnet.save()
    AuditLog.log(user, "Magnet defunct", resource=magnet)
    return model_serializer(magnet)


@router.delete("/api/magnets/{id}")
def destroy(id: int, user=Depends(get_user("delete"))):
    magnet = Magnet.objects \
        .prefetch_related('magnetpart_set__part', 'sitemagnet_set__site', 'cadattachment_set__attachment') \
        .get(id=id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    magnet.delete()
    AuditLog.log(user, "Magnet deleted", resource=magnet)
    return model_serializer(magnet)
