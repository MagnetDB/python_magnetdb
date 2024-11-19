from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse

from ...dependencies import get_user
from ...models import AuditLog
from ...models.storage_attachment import StorageAttachment

router = APIRouter()


@router.get("/api/attachments/{id}/download")
def download(id: int, user=Depends(get_user('read'))):
    attachment = StorageAttachment.objects.filter(id=id).get()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return StreamingResponse(attachment.download(), media_type=attachment.content_type, headers={
        'content-disposition': f'attachment; filename="{attachment.filename}"'
    })

class FilePayload(BaseModel):
    filename: str
    content_type: str
    fileno: int

@router.post("/api/attachments")
def upload(file: UploadFile = File(...), user=Depends(get_user('create'))):
    attached = StorageAttachment.upload(file)
    attached.save()
    AuditLog.log(user, f"Attachment created {file.filename}", resource=attached)
    return attached.serialize()
