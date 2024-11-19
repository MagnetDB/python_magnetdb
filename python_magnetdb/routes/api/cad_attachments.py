from fastapi import APIRouter, UploadFile, Depends, File, HTTPException, Form

from python_magnetdb.dependencies import get_user
from python_magnetdb.models import Magnet, Part, CadAttachment, StorageAttachment, Site
from python_magnetdb.routes.api.serializers import model_serializer

router = APIRouter()


@router.post("/api/cad_attachments")
def create(resource_id: str = Form(...), resource_type: str = Form(...),
            file: UploadFile = File(...), user=Depends(get_user('update'))):
    cad_attachment = CadAttachment()
    if resource_type == 'magnet':
        cad_attachment.magnet = Magnet.objects.get(id=resource_id)
        if not cad_attachment.magnet:
            raise HTTPException(status_code=404, detail="Magnet not found")
    elif resource_type == 'part':
        cad_attachment.part = Part.objects.get(id=resource_id)
        if not cad_attachment.part:
            raise HTTPException(status_code=404, detail="Part not found")
    elif resource_type == 'site':
        cad_attachment.site = Site.objects.get(id=resource_id)
        if not cad_attachment.site:
            raise HTTPException(status_code=404, detail="Site not found")
    else:
        raise HTTPException(status_code=404, detail="Resource not found")
    cad_attachment.attachment = StorageAttachment.upload(file)
    cad_attachment.save()
    return model_serializer(cad_attachment)


@router.delete("/api/cad_attachments/{id}")
def destroy(id: int, user=Depends(get_user('update'))):
    cad_attachment = CadAttachment.objects.get(id=id)
    if not cad_attachment:
        raise HTTPException(status_code=404, detail="CAD Attachment not found")

    cad_attachment.delete()
    return model_serializer(cad_attachment)
