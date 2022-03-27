from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Form, UploadFile, File, Depends

from ...dependencies import get_user
from ...models.attachment import Attachment
from ...models.audit_log import AuditLog
from ...models.magnet import Magnet
from ...models.material import Material

router = APIRouter()


@router.get("/api/magnets")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query(None), sort_desc: bool = Query(False)):
    magnets = Magnet
    if query is not None and query.strip() != '':
        magnets = magnets.where('name', 'ilike', f'%{query}%')
    if sort_by is not None:
        magnets = magnets.order_by(sort_by, 'desc' if sort_desc else 'asc')
    magnets = magnets.paginate(per_page, page)
    return {
        "current_page": magnets.current_page,
        "last_page": magnets.last_page,
        "total": magnets.total,
        "items": magnets.serialize(),
    }


@router.post("/api/magnets")
def create(user=Depends(get_user('create')), name: str = Form(...), description: str = Form(None),
           design_office_reference: str = Form(None), cao: UploadFile = File(None), geometry: UploadFile = File(None)):
    magnet = Magnet(name=name, description=description, design_office_reference=design_office_reference,
                    status='in_study')
    if cao:
        magnet.cao().associate(Attachment.upload(cao))
    if geometry:
        magnet.geometry().associate(Attachment.upload(geometry))
    magnet.save()
    AuditLog.log(user, "Magnet created", resource=magnet)
    return magnet.serialize()


@router.get("/api/magnets/{id}")
def show(id: int, user=Depends(get_user('read'))):
    magnet = Magnet.with_('magnet_parts.part', 'site_magnets.site', 'cao', 'geometry').find(id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")
    return magnet.serialize()


@router.get("/api/magnets/{id}/config")
def show(id: int):
    magnet = Magnet.with_('magnet_parts.part.geometry', 'magnet_parts.part.material', 'site_magnets.site', 'cao', 'geometry').find(id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    def format_material(material):
        return {
            "Tref": material.t_ref,
            "VolumicMass": material.volumic_mass,
            "alpha": material.alpha,
            "ElectricalConductivity": material.electrical_conductivity,
            "MagnetPermeability": material.magnet_permeability,
            "Poisson": material.poisson,
            "Rpe": material.rpe,
            "SpecificHeat": material.specific_heat,
            "ThermalConductivity": material.thermal_conductivity,
            "Young": material.young,
            "CoefDilatation": material.expansion_coefficient,
            "nuance": material.nuance
        }

    payload = {'geom': magnet.geometry.filename}
    insulator_payload = format_material(Material.where('name', 'MAT_ISOLANT').first())

    for magnet_part in magnet.magnet_parts:
        if not magnet_part.active:
            continue

        if magnet_part.part.type.capitalize() not in payload:
            payload[magnet_part.part.type.capitalize()] = []
        payload[magnet_part.part.type.capitalize()].append({
            'geom': magnet_part.part.geometry.filename,
            'material': format_material(magnet_part.part.material),
            'insulator': insulator_payload
        })

    return payload

@router.patch("/api/magnets/{id}")
def update(id: int, user=Depends(get_user('update')), name: str = Form(...), description: str = Form(None),
           design_office_reference: str = Form(None), cao: UploadFile = File(None), geometry: UploadFile = File(None)):
    magnet = Magnet.with_('cao', 'geometry').find(id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    magnet.name = name
    magnet.description = description
    magnet.design_office_reference = design_office_reference
    if cao:
        magnet.cao().associate(Attachment.upload(cao))
    if geometry:
        magnet.geometry().associate(Attachment.upload(geometry))
    magnet.save()
    AuditLog.log(user, "Magnet updated", resource=magnet)
    return magnet.serialize()


@router.post("/api/magnets/{id}/defunct")
def defunct(id: int, user=Depends(get_user('update'))):
    magnet = Magnet.with_('magnet_parts.part').find(id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")

    for magnet_part in magnet.magnet_parts:
        magnet_part.part.status = 'in_stock'
        magnet_part.part.save()
        magnet_part.decommissioned_at = datetime.now()
        magnet_part.save()

    magnet.status = 'defunct'
    magnet.save()
    AuditLog.log(user, "Magnet defunct", resource=magnet)
    return magnet.serialize()


@router.delete("/api/magnets/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    magnet = Magnet.find(id)
    if not magnet:
        raise HTTPException(status_code=404, detail="Magnet not found")
    magnet.delete()
    AuditLog.log(user, "Magnet deleted", resource=magnet)
    return magnet.serialize()
