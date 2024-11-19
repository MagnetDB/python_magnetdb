from typing import Optional

from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from .serializers import model_serializer
from ...dependencies import get_user
from ...models import AuditLog
from ...models.material import Material

router = APIRouter()


class MaterialPayload(BaseModel):
    name: str
    description: Optional[str]
    nuance: Optional[str]
    t_ref: Optional[float] = 20
    volumic_mass: Optional[float] = 0
    alpha: Optional[float] = 0
    specific_heat: Optional[float] = 0
    electrical_conductivity: Optional[float] = 0
    thermal_conductivity: Optional[float] = 0
    magnet_permeability: Optional[float] = 0
    young: Optional[float] = 0
    poisson: Optional[float] = 0
    expansion_coefficient: Optional[float] = 0
    rpe: float


@router.get("/api/materials")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query(None), sort_desc: bool = Query(False)):
    db_query = Material.objects
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


@router.post("/api/materials")
def create(payload: MaterialPayload, user=Depends(get_user('create'))):
    material = Material(
        name=payload.name,
        description=payload.description,
        nuance=payload.nuance,
        t_ref=payload.t_ref,
        volumic_mass=payload.volumic_mass,
        alpha=payload.alpha,
        specific_heat=payload.specific_heat,
        electrical_conductivity=payload.electrical_conductivity,
        thermal_conductivity=payload.thermal_conductivity,
        magnet_permeability=payload.magnet_permeability,
        young=payload.young,
        poisson=payload.poisson,
        expansion_coefficient=payload.expansion_coefficient,
        rpe=payload.rpe,
    )
    try:
        material.save()
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail="Name already taken.") if 'materials_name_unique' in str(e) else e
    AuditLog.log(user, "Material created", resource=material)
    return model_serializer(material)


@router.get("/api/materials/{id}")
def show(id: int, user=Depends(get_user('read'))):
    material = Material.objects.filter(id=id).prefetch_related('part_set').get()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return model_serializer(material)


@router.patch("/api/materials/{id}")
def update(id: int, payload: MaterialPayload, user=Depends(get_user('update'))):
    material = Material.objects.filter(id=id).prefetch_related('part_set').get()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(material, key, value)
    AuditLog.log(user, "Material updated", resource=material)
    return model_serializer(material)


@router.delete("/api/materials/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    material = Material.objects.filter(id=id).prefetch_related('part_set').get()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    material.delete()
    AuditLog.log(user, "Material deleted", resource=material)
    return model_serializer(material)
