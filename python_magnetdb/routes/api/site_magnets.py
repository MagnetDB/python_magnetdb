from datetime import datetime

from fastapi import APIRouter, HTTPException, Form, Depends

from .serializers import model_serializer
from ...dependencies import get_user
from ...models import Site, Magnet, AuditLog, SiteMagnet
from ...models.status import Status

router = APIRouter()


@router.post("/api/sites/{site_id}/magnets")
def create(site_id: int, user=Depends(get_user('create')), magnet_id: int = Form(...)):
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

    site_magnet = SiteMagnet(commissioned_at=datetime.now(), site=site, magnet=magnet)
    site_magnet.save()
    AuditLog.log(user, "Magnet added to site", resource=magnet)
    return model_serializer(site_magnet)
