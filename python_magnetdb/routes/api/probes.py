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
from ...models import Magnet, Part, Probe, AuditLog
from ...models.probe import ProbeType

router = APIRouter()


@router.get("/api/probes")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query("created_at"), sort_desc: bool = Query(False),
          status: List[str] = Query(default=None, alias="status[]"),
          type: List[str] = Query(default=None, alias="type[]")):
    db_query = Probe.objects
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


# TODO add magnet like material for part
@router.post("/api/probes")
def create(
    user=Depends(get_user('create')), 
    name: str = Form(...), 
    description: str = Form(None),
    type: ProbeType = Form(...), 
    index: list = Form(...),
    locations: list = Form(...),
    magnet_id: str = Form(...),
    part_id: str = Form(None),  
    metadata: str = Form('{}')
):
    locations = None
    if not locations:
        raise HTTPException(status_code=404, detail="Locations not found")

    magnet = Magnet.objects.filter(id=magnet_id).get()
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")
    
    part = Part.objects.filter(id=part_id).get() if part_id else None
    if part_id and not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    probe = probe(
        name=name,
        description=description,
        type=type,
        index=index,
        magnet=magnet,
        part=part,
        locations=locations,
        metadata=json.loads(metadata),
    )
    try:
        probe.save()
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail="Name already taken.") if 'probes_name_unique' in str(e) else e
    AuditLog.log(user, "probe created", resource=probe)
    return model_serializer(probe)




@router.get("/api/probes/{id}")
def show(id: int, user=Depends(get_user('read'))):
    probe = probe.objects\
        .select_related('magnet', 'part')\
        .get(id=id)
    if not probe:
        raise HTTPException(status_code=404, detail="probe not found")

    return model_serializer(probe)


@router.patch("/api/probes/{id}")
def update(
    id: int, user=Depends(get_user('update')), 
    name: str = Form(...), 
    description: str = Form(None),
    type: ProbeType = Form(...),  
    index: list = Form(...),
    locations: list = Form(...),
    magnet_id: str = Form(...),
    part_id: str = Form(None),  
    metadata: str = Form(None),
):
    # TODO: correct 
    probe = probe.objects \
        .select_related('magnet', 'part') \
        .get(id=id)
    if not probe:
        raise HTTPException(status_code=404, detail="probe not found")

    locations = None
    if not locations:
        raise HTTPException(status_code=404, detail="Material not found")

    magnet = Magnet.objects.filter(id=magnet_id).get()
    part = Part.objects.filter(id=part_id).get() if part_id else None

    probe.name = name
    probe.description = description
    probe.type = type
    probe.magnet = magnet
    probe.part = part
    if index is not None:
        probe.index = index
    if locations is not None:
        probe.locations = locations
    if metadata is not None:
        probe.metadata = json.loads(metadata)
    probe.save()
    AuditLog.log(user, "probe updated", resource=probe)
    return model_serializer(probe)



@router.delete("/api/probes/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    probe = probe.objects.get(id=id)
    if not probe:
        raise HTTPException(status_code=404, detail="probe not found")

    probe.delete()
    AuditLog.log(user, "probe deleted", resource=probe)
    return model_serializer(probe)
