import shutil
import tempfile
from uuid import uuid4

from django.db import models
from fastapi import UploadFile

from python_magnetdb.storage import s3_client, s3_bucket


class StorageAttachment(models.Model):
    class Meta:
        db_table = 'storage_attachments'
    id = models.BigAutoField(primary_key=True)
    filename = models.CharField(max_length=255, null=True)
    content_type = models.CharField(max_length=255, null=True)
    key = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    def download(self, path=None):
        if path is not None:
            return s3_client.fget_object(s3_bucket, self.key, path)
        return s3_client.get_object(s3_bucket, self.key)

    @classmethod
    def upload(cls, file: UploadFile):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            return cls.raw_upload(file.filename, file.content_type, temp_file.name)

    @classmethod
    def raw_upload(cls, filename: str, content_type: str, fileno: int | str):
        attachment = cls(
            key=str(uuid4()),
            filename=filename,
            content_type=content_type,
        )
        s3_client.fput_object(s3_bucket, attachment.key, fileno, content_type=attachment.content_type)
        attachment.save()
        return attachment
