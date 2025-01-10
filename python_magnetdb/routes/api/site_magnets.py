from datetime import datetime

from fastapi import APIRouter, HTTPException, Form, Depends

from .serializers import model_serializer
from ...dependencies import get_user
from ...models import Site, Magnet, AuditLog, SiteMagnet
from ...models.status import Status

router = APIRouter()


@router.post("/api/site_magnets")
def create(
    user=Depends(get_user('create')), site_id: int = Form(...),  magnet_id: int = Form(...),
    z_offset: float = Form(None), r_offset: float = Form(None), parallax: float = Form(None),
):
    site = Site.objects.get(id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    magnet = Magnet.objects.prefetch_related('sitemagnet_set__site').get(id=magnet_id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    for site_magnet in magnet.sitemagnet_set.all():
        if site_magnet.site.status == Status.IN_STUDY:
            site_magnet.delete()
            AuditLog.log(user, "Magnet detached from Site", resource=magnet)

    site_magnet = SiteMagnet(
        commissioned_at=datetime.now(), site=site, magnet=magnet,
        z_offset=z_offset, r_offset=r_offset, parallax=parallax
    )
    site_magnet.save()
    AuditLog.log(user, "Magnet added to site", resource=magnet)
    return model_serializer(site_magnet)


@router.delete("/api/site_magnets/{sitemagnet_id}")
def destroy(sitemagnet_id: int, user=Depends(get_user("delete"))):
    site_magnet = SiteMagnet.objects.select_related('site').get(id=sitemagnet_id)
    if not site_magnet:
        raise HTTPException(status_code=404, detail="Site magnet not found")

    if site_magnet.site.status != Status.IN_STUDY and site_magnet.site.status != Status.IN_STOCK:
        raise HTTPException(status_code=422, detail="Site not editable")

    site_magnet.delete()
    AuditLog.log(user, "Magnet deleted to site", resource=site_magnet)
    return model_serializer(site_magnet)
