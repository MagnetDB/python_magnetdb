from fastapi import APIRouter, UploadFile, Depends, File, HTTPException, Form

from python_magnetdb.dependencies import get_user
from python_magnetdb.models import Magnet, StorageAttachment, Site, MeshAttachment
from python_magnetdb.models.mesh_attachment import MeshAttachmentType
from python_magnetdb.routes.api.serializers import model_serializer

router = APIRouter()


@router.post("/api/mesh_attachments")
def create(resource_id: str = Form(...), resource_type: str = Form(...), type: MeshAttachmentType = Form(...),
           file: UploadFile = File(...), user=Depends(get_user('update'))):
    mesh_attachment = MeshAttachment()
    if resource_type == 'magnet':
        mesh_attachment.magnet = Magnet.objects.get(id=resource_id)
        if not mesh_attachment.magnet:
            raise HTTPException(status_code=404, detail="Magnet not found")
    elif resource_type == 'site':
        mesh_attachment.site = Site.objects.get(id=resource_id)
        if not mesh_attachment.site:
            raise HTTPException(status_code=404, detail="Site not found")
    else:
        raise HTTPException(status_code=404, detail="Resource not found")
    mesh_attachment.type = type
    mesh_attachment.attachment = StorageAttachment.upload(file)
    mesh_attachment.save()
    return model_serializer(mesh_attachment)


@router.delete("/api/mesh_attachments/{id}")
def destroy(id: int, user=Depends(get_user('update'))):
    mesh_attachment = MeshAttachment.objects.get(id=id)
    if not mesh_attachment:
        raise HTTPException(status_code=404, detail="Mesh attachment not found")

    mesh_attachment.delete()
    return model_serializer(mesh_attachment)
