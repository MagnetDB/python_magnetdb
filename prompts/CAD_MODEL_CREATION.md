# Task: Create the standalone `Cad` model

## Context

MagnetDB currently manages CAD files through a thin `CadAttachment` model that holds
a direct foreign key to a `Part`, `Magnet`, or `Site`. This model has no support for
sharing a CAD file across multiple objects, and captures no provenance metadata.

The goal is to introduce a **new, standalone `Cad` model** that coexists with
`CadAttachment` (which must not be modified or deleted). Migration is intentionally
additive: existing `CadAttachment` rows are backfilled into `Cad` during the data
migration, but the old table and all existing code using it remain fully functional.

This task follows the same pattern as the `Mesh` model creation. Read
`MESH_MODEL_CREATION.md` first if you need to understand the shared approach.

---

## Target model definition

File: `python_magnetdb/models/cad.py`

```python
import enum
from django.db import models


class CadType(str, enum.Enum):
    AXI = 'axi'
    THREE_DIMENSIONS = '3d'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Cad(models.Model):
    """
    First-class CAD object, replacing the thin CadAttachment join model.

    Provenance schema (stored in the `provenance` JSONField):
    {
        "tool":        "python_magnetgeo",   # tool or script name
        "version":     "0.4.2",              # pip version or git tag
        "commit":      "a3f9c12",            # git SHA if available
        "inputs": {
            "geometry": "HL-31-HR.yaml",     # input files by name
            "config":   "salome_cfg.yaml"
        },
        "environment": {
            "salome":  "9.11.0",
            "opencascade": "7.6.0"
        },
        "produced_at": "2025-03-15T10:42:00Z"  # ISO 8601 generation timestamp
    }

    CAD files typically come in pairs (.xao + .brep for a given geometry).
    Each file is a separate `Cad` row sharing the same owners, distinguished
    by filename on the linked `StorageAttachment`.
    """
    class Meta:
        db_table = 'cad'

    id         = models.BigAutoField(primary_key=True)
    type       = models.CharField(
                   max_length=255,
                   null=False,
                   choices=CadType.choices(),
                   default=CadType.THREE_DIMENSIONS
                 )
    attachment = models.ForeignKey(
                   'StorageAttachment',
                   on_delete=models.CASCADE,
                   null=False
                 )
    cad_config = models.JSONField(null=True)   # salome/gmsh parameters
    command    = models.CharField(max_length=1024, null=True)  # CLI used to generate
    provenance = models.JSONField(null=True)   # see schema above
    comment    = models.TextField(null=True)

    # Many-to-many: one Cad file can be shared; one object can have many Cad files
    parts      = models.ManyToManyField('Part',   blank=True, related_name='cad_set')
    magnets    = models.ManyToManyField('Magnet', blank=True, related_name='cad_set')
    sites      = models.ManyToManyField('Site',   blank=True, related_name='cad_set')

    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
```

**Note on naming:** The M2M reverse accessor on `Part` is `cad_set` (not `cads`) to
avoid collision with any future `cad` property. This is consistent with Django
conventions for reverse M2M accessors.

---

## Step 1 — Register the model

In `python_magnetdb/models/__init__.py`, add:

```python
from .cad import Cad, CadType
```

---

## Step 2 — Django migration

Generate with:
```bash
python manage.py makemigrations
```

This will create a migration that:
- Creates the `cad` table
- Creates the M2M through tables: `cad_parts`, `cad_magnets`, `cad_sites`

**Then add a data migration** as a separate migration file to backfill existing
`CadAttachment` rows into the new `Cad` table:

```python
from django.db import migrations


def backfill_cad_from_cad_attachment(apps, schema_editor):
    CadAttachment = apps.get_model('python_magnetdb', 'CadAttachment')
    Cad = apps.get_model('python_magnetdb', 'Cad')

    for ca in CadAttachment.objects.select_related('attachment', 'part', 'magnet', 'site').all():
        cad = Cad.objects.create(
            type=ca.type,
            attachment=ca.attachment,
            # cad_config, command, provenance, comment all NULL:
            # this is honest — that information was never captured.
            # Fill these in progressively as CAD files are regenerated.
        )
        if ca.part_id:
            cad.parts.add(ca.part)
        if ca.magnet_id:
            cad.magnets.add(ca.magnet)
        if ca.site_id:
            cad.sites.add(ca.site)


class Migration(migrations.Migration):
    dependencies = [
        ('python_magnetdb', '<previous_migration>'),  # replace with actual
    ]

    operations = [
        migrations.RunPython(
            backfill_cad_from_cad_attachment,
            migrations.RunPython.noop  # no rollback — old table is untouched
        ),
    ]
```

---

## Step 3 — FastAPI routes

File: `python_magnetdb/routes/api/cad.py`

Implement the following endpoints. Follow the style of the existing
`cad_attachments.py` router for consistency.

### `POST /api/cad`

Creates a new `Cad` with an uploaded file, and links it to one owner.

Form fields:
- `file: UploadFile` — the CAD file (`.xao`, `.brep`, or other)
- `type: CadType` — `'axi'` or `'3d'`
- `cad_config: str | None` — JSON string of CAD generation parameters (optional)
- `command: str | None` — CLI command used to generate this file (optional)
- `provenance: str | None` — JSON string matching the provenance schema (optional)
- `comment: str | None` — free-text comment (optional)
- `resource_type: str` — `'part'`, `'magnet'`, or `'site'`
- `resource_id: int`

```python
@router.post("/api/cad")
def create(
    resource_id: int = Form(...),
    resource_type: str = Form(...),
    type: CadType = Form(...),
    file: UploadFile = File(...),
    cad_config: str = Form(None),
    command: str = Form(None),
    provenance: str = Form(None),
    comment: str = Form(None),
    user=Depends(get_user('update'))
):
    cad = Cad(type=type, command=command, comment=comment)
    cad.attachment = StorageAttachment.upload(file)
    if cad_config:
        cad.cad_config = json.loads(cad_config)
    if provenance:
        cad.provenance = json.loads(provenance)
    cad.save()

    if resource_type == 'magnet':
        magnet = Magnet.objects.get(id=resource_id)
        cad.magnets.add(magnet)
    elif resource_type == 'site':
        site = Site.objects.get(id=resource_id)
        cad.sites.add(site)
    elif resource_type == 'part':
        part = Part.objects.get(id=resource_id)
        cad.parts.add(part)
    else:
        raise HTTPException(status_code=400, detail="Invalid resource_type")

    return model_serializer(cad)
```

### `GET /api/cad/{id}`

Returns a single `Cad` with its `attachment` relation included.

### `PATCH /api/cad/{id}`

Allows updating `cad_config`, `command`, `provenance`, `comment`.
Does **not** allow changing `type` or `attachment` (those are immutable once created).

### `DELETE /api/cad/{id}`

Deletes the `Cad` row. The `StorageAttachment` is cascade-deleted by the FK constraint.

### `POST /api/cad/{id}/link`

Links an existing `Cad` to an additional owner (exploits the sharing capability).

Form fields: `resource_type: str`, `resource_id: int`

### `DELETE /api/cad/{id}/unlink`

Removes the M2M link between a `Cad` and one owner.
Deletes the `Cad` row itself only if it has no remaining owners.

Form fields: `resource_type: str`, `resource_id: int`

---

## Step 4 — Register the router

In `python_magnetdb/routes/api/__init__.py` (or wherever routers are registered
in `web.py`), include:

```python
from .cad import router as cad_router
app.include_router(cad_router)
```

---

## Step 5 — Update serializers and show endpoints

### Serializer

The `model_serializer` function uses Django's `ReverseManyToOneDescriptor`
introspection. The M2M reverse accessors will be serialized automatically once
`prefetch_related` is set up correctly. Verify serialized output for a `Cad` instance.

### Part show endpoint (`routes/api/parts.py`)

Update `prefetch_related` in the `show` and `update` endpoints:

```python
.prefetch_related(
    ...,
    'cad_set__attachment',         # new Cad M2M
    'cadattachment_set__attachment',  # keep — old model still active
)
```

Update `_part_post_processor` in `serializers.py`:

```python
if 'cad_set' in res:
    res['cad_new'] = res['cad_set']   # expose as 'cad' once CadAttachment is retired
    del res['cad_set']
if 'cadattachment_set' in res:
    res['cad'] = res['cadattachment_set']  # existing key, keep unchanged
    del res['cadattachment_set']
```

### Magnet show endpoint (`routes/api/magnets.py`)

Same pattern — add `'cad_set__attachment'` to `prefetch_related`.
Update `_magnet_post_processor` to expose both old and new CAD relations.

### Site show endpoint (`routes/api/sites.py`)

Same pattern — add `'cad_set__attachment'` to `prefetch_related`.
Update `_site_post_processor` accordingly.

---

## Note on CAD file pairs

In the existing system, a single geometry produces two files: `.xao` and `.brep`.
Each is currently stored as a separate `CadAttachment` row pointing to the same
owner. In the new `Cad` model this is preserved — each file remains a separate `Cad`
row. They are implicitly related by sharing the same owners and the same `command` /
`provenance` fields (both were produced by the same invocation).

If explicit pairing becomes important in the future, a `group_id` UUID field could be
added to `Cad` to link files produced by the same run. This is **out of scope** for
this task.

---

## What must NOT be changed

- `python_magnetdb/models/cad_attachment.py` — do not modify
- `python_magnetdb/routes/api/cad_attachments.py` — do not modify
- All existing `cadattachment_set` prefetch calls — keep them alongside the new ones
- Frontend `CadAttachment` components — do not modify

---

## Acceptance criteria

- [ ] `Cad` model exists with all fields and M2M relations to `Part`, `Magnet`, `Site`
- [ ] Django migration creates `cad` table and M2M through tables without errors
- [ ] Data migration backfills all existing `CadAttachment` rows into `Cad`
- [ ] `POST /api/cad` creates a `Cad` row and links it to the given owner
- [ ] `GET /api/parts/{id}` response exposes both `cad` (old `cadattachment_set`) and `cad_new` (new M2M)
- [ ] `GET /api/magnets/{id}` and `GET /api/sites/{id}` similarly expose both
- [ ] `POST /api/cad/{id}/link` adds a second owner to an existing `Cad` row
- [ ] `DELETE /api/cad/{id}/unlink` removes an owner link; deletes the row if no owners remain
- [ ] All existing tests pass — nothing using `CadAttachment` is broken
