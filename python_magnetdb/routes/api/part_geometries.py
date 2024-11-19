from fastapi import APIRouter, HTTPException, Depends, UploadFile
from fastapi.params import Form, File

from .serializers import model_serializer
from ...dependencies import get_user
from ...models import Part, PartGeometry, StorageAttachment, AuditLog

router = APIRouter()


@router.post("/api/parts/{part_id}/geometries")
def create(part_id: int, type: str = Form(...), attachment: UploadFile = File(...), user=Depends(get_user('create'))):
    part = Part.objects.get(id=part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    if not type in part.allow_geometry_types():
        raise HTTPException(status_code=422, detail=f"Unsupported type for {part.type}")

    geometry = PartGeometry.objects.filter(part_id=part_id, type=type).first()
    if not geometry:
        geometry = PartGeometry(part_id=part_id, type=type)
    geometry.attachment = StorageAttachment.upload(attachment)
    geometry.save()
    AuditLog.log(user, "Geometry saved", resource=geometry)
    return model_serializer(geometry)


@router.delete("/api/parts/{part_id}/geometries/{type}")
def destroy(part_id: int, type: str, user=Depends(get_user('delete'))):
    geometry = PartGeometry.objects.filter(part_id=part_id, type=type).first()
    if not geometry:
        raise HTTPException(status_code=404, detail="Geometry not found")

    geometry.delete()
    AuditLog.log(user, "Geometry deleted", resource=geometry)
    return model_serializer(geometry)
