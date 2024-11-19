from datetime import datetime
from typing import List

from django.core.paginator import Paginator
from django.db import IntegrityError
from fastapi import Depends, APIRouter, HTTPException, Query, UploadFile, File, Form

from .serializers import model_serializer
from ...actions.generate_simulation_config import generate_site_config
from ...dependencies import get_user
from ...models import StorageAttachment
from ...models.audit_log import AuditLog
from ...models.site import Site
from ...models.status import Status

router = APIRouter()


@router.get("/api/sites")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query('created_at'), sort_desc: bool = Query(False),
          status: List[str] = Query(default=None, alias="status[]")):
    db_query = Site.objects.prefetch_related('sitemagnet_set__magnet')
    if sort_by is not None:
        order_field = f"-{sort_by}" if sort_desc else sort_by
        db_query = db_query.order_by(order_field)
    if query is not None and query.strip() != '':
        db_query = db_query.filter(name__icontains=query)
    if status is not None:
        db_query = db_query.filter(status__in=status)
    paginator = Paginator(db_query.all(), per_page)
    items = [model_serializer(site) for site in paginator.get_page(page).object_list]

    return {
        "current_page": page,
        "last_page": paginator.num_pages,
        "total": paginator.count,
        "items": items,
    }


@router.post("/api/sites")
def create(user=Depends(get_user('create')), name: str = Form(...), description: str = Form(None),
           config: UploadFile = File(None)):
    site = Site(name=name, description=description, status=Status.IN_STUDY)
    if config is not None:
        site.config_attachment = StorageAttachment.upload(config)
    try:
        site.save()
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail="Name already taken.") if 'sites_name_unique' in str(e) else e
    AuditLog.log(user, "Site created", resource=site)
    return model_serializer(site)


@router.get("/api/sites/{id}")
def show(id: int, user=Depends(get_user('read'))):
    site = Site.objects.prefetch_related('sitemagnet_set__magnet', 'record_set', 'config_attachment').get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return model_serializer(site)


@router.patch("/api/sites/{id}")
def update(id: int, user=Depends(get_user('update')), name: str = Form(...), description: str = Form(None),
           config: UploadFile = File(None)):
    site = Site.objects.prefetch_related('sitemagnet_set__magnet', 'record_set', 'config_attachment').get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.name = name
    site.description = description
    if config:
        site.config_attachment = StorageAttachment.upload(config)
    site.save()
    AuditLog.log(user, "Site updated", resource=site)
    return model_serializer(site)

@router.get("/api/sites/{id}/records")
def records(id: int, user=Depends(get_user('read'))):
    site = Site.objects.prefetch_related('record_set').get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    result = []
    for record in site.record_set.all():
        result.append(model_serializer(record))
    return {'records': result}

@router.get("/api/sites/{id}/mdata")
def mdata(id: int, user=Depends(get_user('read'))):
    site = Site.objects.get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    data = generate_site_config(id)
    print(f'/api/sites/{id}/mdata: {data}')
    return {'results': data}

@router.post("/api/sites/{id}/put_in_operation")
def put_in_operation(id: int, commissioned_at: datetime = Form(datetime.now()), user=Depends(get_user('update'))):
    site = Site.objects.prefetch_related('sitemagnet_set__magnet__magnetpart_set__part').get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    for site_magnet in site.sitemagnet_set.all():
        if not site_magnet.active:
            continue
        site_magnet.magnet.status = Status.IN_OPERATION
        site_magnet.magnet.save()
        site_magnet.commissioned_at = commissioned_at
        site_magnet.save()
        for magnet_part in site_magnet.magnet.magnetpart_set.all():
            if not magnet_part.active:
                continue
            magnet_part.part.status = Status.IN_OPERATION
            magnet_part.part.save()
            magnet_part.commissioned_at = commissioned_at
            magnet_part.save()

    site.status = Status.IN_OPERATION
    site.save()
    AuditLog.log(user, "Site put in operation", resource=site)
    return model_serializer(site)


@router.post("/api/sites/{id}/shutdown")
def shutdown(id: int, decommissioned_at: datetime = Form(datetime.now()), user=Depends(get_user('update'))):
    site = Site.objects.prefetch_related('sitemagnet_set__magnet').get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    for site_magnet in site.sitemagnet_set.all():
        if not site_magnet.active:
            continue
        site_magnet.magnet.status = Status.IN_STOCK
        site_magnet.magnet.save()
        site_magnet.decommissioned_at = decommissioned_at
        site_magnet.save()

    site.status = Status.DEFUNCT
    site.save()
    AuditLog.log(user, "Site shutdown", resource=site)
    return model_serializer(site)


@router.delete("/api/sites/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    site = Site.objects.prefetch_related('sitemagnet_set__magnet', 'record_set', 'config_attachment').get(id=id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.delete()
    AuditLog.log(user, "Site deleted", resource=site)
    return model_serializer(site)
