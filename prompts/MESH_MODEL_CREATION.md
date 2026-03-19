# Task: Create the standalone `Mesh` model

## Context

MagnetDB currently manages mesh files through a thin `MeshAttachment` model that holds
a direct foreign key to either a `Magnet` or a `Site`. This model has no support for
sharing a mesh across multiple objects, and captures no provenance metadata.

The goal is to introduce a **new, standalone `Mesh` model** that coexists with
`MeshAttachment` (which must not be modified or deleted). Migration is intentionally
additive: existing `MeshAttachment` rows are backfilled into `Mesh` during the data
migration, but the old table and all existing code using it remain fully functional.

---

## Target model definition

File: `python_magnetdb/models/mesh.py`

```python
import enum
from django.db import models


class MeshType(str, enum.Enum):
    AXI = 'axi'
    THREE_DIMENSIONS = '3d'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Mesh(models.Model):
    """
    First-class mesh object, replacing the thin MeshAttachment join model.

    Provenance schema (stored in the `provenance` JSONField):
    {
        "tool":        "python_magnetgeo",   # tool or script name
        "version":     "0.4.2",              # pip version or git tag
        "commit":      "a3f9c12",            # git SHA if available
        "inputs": {
            "geometry": "HL-31-HR.yaml",     # input files by name
            "config":   "mesh_cfg_axi.yaml"
        },
        "environment": {
            "salome": "9.11.0",
            "gmsh":   "4.12.1"
        },
        "produced_at": "2025-03-15T10:42:00Z"  # ISO 8601 generation timestamp
    }
    """
    class Meta:
        db_table = 'meshes'

    id          = models.BigAutoField(primary_key=True)
    type        = models.CharField(
                    max_length=255,
                    null=False,
                    choices=MeshType.choices()
                  )
    attachment  = models.ForeignKey(
                    'StorageAttachment',
                    on_delete=models.CASCADE,
                    null=False
                  )
    mesh_config = models.JSONField(null=True)   # parsed yaml mesh cfg
    command     = models.CharField(max_length=1024, null=True)  # CLI used to generate
    provenance  = models.JSONField(null=True)   # see schema above
    comment     = models.TextField(null=True)

    # Many-to-many: one Mesh can be shared; one object can have many Meshes
    parts       = models.ManyToManyField('Part',   blank=True, related_name='meshes')
    magnets     = models.ManyToManyField('Magnet', blank=True, related_name='meshes')
    sites       = models.ManyToManyField('Site',   blank=True, related_name='meshes')

    created_at  = models.DateTimeField(auto_now_add=True, null=False)
    updated_at  = models.DateTimeField(auto_now=True, null=False)
```

---

## Step 1 — Register the model

In `python_magnetdb/models/__init__.py`, add:

```python
from .mesh import Mesh, MeshType
```

---

## Step 2 — Django migration

Generate with:
```bash
python manage.py makemigrations
```

This will create a migration that:
- Creates the `meshes` table
- Creates the M2M through tables: `meshes_parts`, `meshes_magnets`, `meshes_sites`

**Then add a data migration** as a second step (separate migration file) to backfill
existing `MeshAttachment` rows into the new `Mesh` table:

```python
from django.db import migrations


def backfill_mesh_from_mesh_attachment(apps, schema_editor):
    MeshAttachment = apps.get_model('python_magnetdb', 'MeshAttachment')
    Mesh = apps.get_model('python_magnetdb', 'Mesh')

    for ma in MeshAttachment.objects.select_related('attachment', 'magnet', 'site').all():
        mesh = Mesh.objects.create(
            type=ma.type,
            attachment=ma.attachment,
            # mesh_config, command, provenance, comment all NULL:
            # this is honest — that information was never captured.
            # Fill these in progressively as meshes are regenerated.
        )
        if ma.magnet_id:
            mesh.magnets.add(ma.magnet)
        if ma.site_id:
            mesh.sites.add(ma.site)


class Migration(migrations.Migration):
    dependencies = [
        ('python_magnetdb', '<previous_migration>'),  # replace with actual
    ]

    operations = [
        migrations.RunPython(
            backfill_mesh_from_mesh_attachment,
            migrations.RunPython.noop  # no rollback — old table is untouched
        ),
    ]
```

---

## Step 3 — FastAPI routes

File: `python_magnetdb/routes/api/meshes.py`

Implement the following endpoints. Follow the style of the existing
`mesh_attachments.py` router for consistency.

### `POST /api/meshes`

Creates a new `Mesh` with an uploaded file, and links it to one or more owners.

Form fields:
- `file: UploadFile` — the mesh file
- `type: MeshType` — `'axi'` or `'3d'`
- `mesh_config: str | None` — JSON string of mesh cfg data (optional)
- `command: str | None` — CLI command used to generate the mesh (optional)
- `provenance: str | None` — JSON string matching the provenance schema (optional)
- `comment: str | None` — free-text comment (optional)
- `resource_type: str` — `'part'`, `'magnet'`, or `'site'`
- `resource_id: int`

```python
@router.post("/api/meshes")
def create(
    resource_id: int = Form(...),
    resource_type: str = Form(...),
    type: MeshType = Form(...),
    file: UploadFile = File(...),
    mesh_config: str = Form(None),
    command: str = Form(None),
    provenance: str = Form(None),
    comment: str = Form(None),
    user=Depends(get_user('update'))
):
    mesh = Mesh(type=type, command=command, comment=comment)
    mesh.attachment = StorageAttachment.upload(file)
    if mesh_config:
        mesh.mesh_config = json.loads(mesh_config)
    if provenance:
        mesh.provenance = json.loads(provenance)
    mesh.save()

    if resource_type == 'magnet':
        magnet = Magnet.objects.get(id=resource_id)
        mesh.magnets.add(magnet)
    elif resource_type == 'site':
        site = Site.objects.get(id=resource_id)
        mesh.sites.add(site)
    elif resource_type == 'part':
        part = Part.objects.get(id=resource_id)
        mesh.parts.add(part)
    else:
        raise HTTPException(status_code=400, detail="Invalid resource_type")

    return model_serializer(mesh)
```

### `GET /api/meshes/{id}`

Returns a single `Mesh` with its `attachment` relation included.

### `PATCH /api/meshes/{id}`

Allows updating `mesh_config`, `command`, `provenance`, `comment`.
Does **not** allow changing `type` or `attachment` (those are immutable once created).

### `DELETE /api/meshes/{id}`

Deletes the `Mesh` row. The `StorageAttachment` is cascade-deleted by the FK constraint.

### `POST /api/meshes/{id}/link`

Links an existing `Mesh` to an additional owner (exploits the sharing capability).

Form fields: `resource_type: str`, `resource_id: int`

### `DELETE /api/meshes/{id}/unlink`

Removes the M2M link between a `Mesh` and one owner.
Deletes the `Mesh` row itself only if it has no remaining owners.

Form fields: `resource_type: str`, `resource_id: int`

---

## Step 4 — Register the router

In `python_magnetdb/routes/api/__init__.py` (or wherever routers are registered
in `web.py`), include:

```python
from .meshes import router as meshes_router
app.include_router(meshes_router)
```

---

## Step 5 — Update serializers and show endpoints

### Serializer

The `model_serializer` function in `serializers.py` uses Django's
`ReverseManyToOneDescriptor` introspection. The M2M reverse accessors
(`part_set`, `magnet_set`, `site_set`) will be serialized automatically.
Verify the serialized output looks correct for a `Mesh` instance.

### Magnet show endpoint (`routes/api/magnets.py`)

Update `prefetch_related` in the `show`, `update`, `defunct`, and `destroy`
endpoints to include the new M2M:

```python
.prefetch_related(
    ...,
    'meshes__attachment',         # new
    'meshattachment_set__attachment',  # keep — old model still active
)
```

Update `_magnet_post_processor` in `serializers.py` to expose both:
```python
if 'meshes' in res:
    res['new_meshes'] = res['meshes']   # or just 'meshes' once MeshAttachment is retired
```

### Site show endpoint (`routes/api/sites.py`)

Same pattern — add `'meshes__attachment'` to `prefetch_related` in the `show` endpoint.
Update `_site_post_processor` accordingly.

### Part show endpoint (`routes/api/parts.py`)

Add `'meshes__attachment'` to `prefetch_related` in the `show` endpoint.
Update `_part_post_processor` to expose `mesh_set`.

---

## Step 6 — Update `Simulation.mesh_attachment` (optional, deferred)

The `Simulation` model currently has a FK to `MeshAttachment`. This can be
migrated to point to `Mesh` in a separate task, once the new model is stable.
For now, leave `Simulation.mesh_attachment` unchanged.

When ready, the migration will:
1. Add `Simulation.mesh = FK(Mesh, null=True)`
2. Data-migrate existing `simulation.mesh_attachment_id` → look up the backfilled
   `Mesh` row that was created from that `MeshAttachment` (match on
   `attachment_id` and owner)
3. Drop `Simulation.mesh_attachment`

---

## What must NOT be changed

- `python_magnetdb/models/mesh_attachment.py` — do not modify
- `python_magnetdb/routes/api/mesh_attachments.py` — do not modify
- `web/src/components/MeshAttachmentEditor.vue` — do not modify
- All existing `meshattachment_set` prefetch calls — keep them alongside the new ones

---

## Acceptance criteria

- [ ] `Mesh` model exists with all fields and M2M relations to `Part`, `Magnet`, `Site`
- [ ] Django migration creates `meshes` table and M2M through tables without errors
- [ ] Data migration backfills all existing `MeshAttachment` rows into `Mesh`
- [ ] `POST /api/meshes` creates a `Mesh` and links it to the given owner
- [ ] `GET /api/magnets/{id}` response includes both `meshes` (new) and `meshes` from `meshattachment_set` (old, kept as `mesh_attachments` key)
- [ ] `GET /api/sites/{id}` and `GET /api/parts/{id}` similarly expose new `meshes`
- [ ] `POST /api/meshes/{id}/link` adds a second owner to an existing mesh
- [ ] `DELETE /api/meshes/{id}/unlink` removes an owner link; deletes the row if no owners remain
- [ ] All existing tests pass — nothing using `MeshAttachment` is broken
