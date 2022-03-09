from datetime import datetime

from fastapi import Depends, APIRouter, HTTPException, Query, UploadFile, File, Form

from ...dependencies import get_user
from ...models.attachment import Attachment
from ...models.log import Log
from ...models.site import Site

router = APIRouter()


@router.get("/api/sites")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100)):
    sites = Site.paginate(per_page, page)
    return {
        "current_page": sites.current_page,
        "last_page": sites.last_page,
        "total": sites.total,
        "items": sites.serialize(),
    }


@router.post("/api/sites")
def create(user=Depends(get_user('create')), name: str = Form(...), description: str = Form(None),
           config: UploadFile = File(...)):
    site = Site(name=name, description=description, status='in_study')
    site.config().associate(Attachment.upload(config))
    site.save()
    Log.log(user, "Site created", object=site)
    return site.serialize()


@router.get("/api/sites/{id}")
def show(id: int, user=Depends(get_user('read'))):
    site = Site.with_('config', 'site_magnets.magnet').find(id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site.serialize()


@router.patch("/api/sites/{id}")
def update(id: int, user=Depends(get_user('update')), name: str = Form(...), description: str = Form(None),
           status: str = Form(...), config: UploadFile = File(None)):
    site = Site.find(id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.name = name
    site.description = description
    site.status = status
    if config:
        site.config().associate(Attachment.upload(config))
    site.save()
    Log.log(user, "Site updated", object=site)
    return site.serialize()


@router.post("/api/sites/{id}/put_in_operation")
def put_in_operation(id: int, user=Depends(get_user('update'))):
    site = Site.with_('site_magnets.magnet.magnet_parts.part').find(id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    for site_magnet in site.site_magnets:
        site_magnet.magnet.status = 'in_operation'
        site_magnet.magnet.save()
        for magnet_part in site_magnet.magnet.magnet_parts:
            magnet_part.part.status = 'in_operation'
            magnet_part.part.save()

    site.status = 'in_operation'
    site.save()
    Log.log(user, "Site put in operation", object=site)
    return site.serialize()


@router.post("/api/sites/{id}/shutdown")
def shutdown(id: int, user=Depends(get_user('update'))):
    site = Site.with_('site_magnets.magnet').find(id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    for site_magnet in site.site_magnets:
        site_magnet.magnet.status = 'in_stock'
        site_magnet.magnet.save()
        site_magnet.decommissioned_at = datetime.now()
        site_magnet.save()

    site.status = 'defunct'
    site.save()
    Log.log(user, "Site shutdown", object=site)
    return site.serialize()


@router.delete("/api/sites/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    site = Site.find(id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site.delete()
    Log.log(user, "Site deleted", object=site)
    return site.serialize()
