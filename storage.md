# MinIO Storage Bucket Creation

## Where the bucket is created

The MinIO bucket (name from `S3_BUCKET` env var, defaults to `"magnetdb"`) is automatically created in [python_magnetdb/storage.py](python_magnetdb/storage.py#L13-L14).

```python
if not s3_client.bucket_exists(s3_bucket):
    s3_client.make_bucket(s3_bucket)
```

This happens at **module import time** - the bucket is created as a side effect when the module is first imported.

## Call Chain

1. **Entry points:**
   - [python_magnetdb/web.py](python_magnetdb/web.py) - FastAPI web server
   - [python_magnetdb/worker.py](python_magnetdb/worker.py) - Celery worker

2. **Import routers/models:**
   - Example: [python_magnetdb/routes/api/sites.py](python_magnetdb/routes/api/sites.py#L14) imports `StorageAttachment`
   - Example: [python_magnetdb/worker.py](python_magnetdb/worker.py#L8) imports `Simulation, Server`

3. **[python_magnetdb/models/__init__.py](python_magnetdb/models/__init__.py#L11)**
   - Exports `StorageAttachment` from `.storage_attachment`

4. **[python_magnetdb/models/storage_attachment.py](python_magnetdb/models/storage_attachment.py#L8)**
   - Imports `s3_client, s3_bucket` from `python_magnetdb.storage`

5. **[python_magnetdb/storage.py](python_magnetdb/storage.py#L13-L14)** ⬅️ **BUCKET CREATED HERE**
   - Automatically checks if bucket exists
   - Creates it if missing

## When the bucket is created

- When the FastAPI web server starts
- When the Celery worker starts
- Anytime code imports models that depend on `StorageAttachment`

## Environment Variables

- `S3_ENDPOINT` - MinIO server endpoint
- `S3_ACCESS_KEY` - MinIO access key
- `S3_SECRET_KEY` - MinIO secret key
- `S3_BUCKET` - Bucket name (default: `magnetdb`)
