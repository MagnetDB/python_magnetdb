from django.db import models
from fastapi import APIRouter

from ...models import Site, Magnet, User, Record

router = APIRouter()


@router.get("/api/home")
def show():
    sites = Site.objects.values('status').annotate(count=models.Count('id')).order_by('status').all()
    magnets = Magnet.objects.values('status').annotate(count=models.Count('id')).order_by('status').all()
    users_count = User.objects.count()
    records_count = Record.objects.count()

    return {
        'sites': list(sites),
        'magnets': list(magnets),
        'users_count': users_count,
        'records_count': records_count,
    }
