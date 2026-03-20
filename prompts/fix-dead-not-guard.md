# Fix dead `if not <obj>:` guards across all route files

## Problem

Throughout `python_magnetdb/routes/api/`, objects are fetched with
`Model.objects.get(id=id)` and then immediately checked with `if not obj:`.
This check is **dead code**: Django's `.get()` never returns `None` — it raises
`Model.DoesNotExist` when no row is found.  As a result, 404 errors are never
returned; instead the server crashes with an unhandled exception.

The correct pattern (already applied to `magnets.py → parts()`) is:

```python
# BEFORE (broken)
obj = Model.objects.get(id=id)
if not obj:
    raise HTTPException(status_code=404, detail="... not found")

# AFTER (correct)
try:
    obj = Model.objects.get(id=id)
except Model.DoesNotExist:
    raise HTTPException(status_code=404, detail="... not found")
```

## Scope — files and approximate line numbers

Apply the fix to **every** occurrence of the dead guard pattern in the
following files (line numbers are approximate — verify before editing):

| File | Variable | Model |
|------|----------|-------|
| `routes/api/magnets.py` | `magnet` | `Magnet` | lines 84, 109, 118, 131, 143, 159, 184, 211, 237 |
| `routes/api/magnet_parts.py` | `magnet`, `part` | `Magnet`, `Part` | lines 22–27 |
| `routes/api/materials.py` | `material` | `Material` | lines 84, 92, 105 |
| `routes/api/parts.py` | `part`, `material` | `Part`, `Material` | lines 68, 95, 110, 130, 158, 162, 217, 226, 238 |
| `routes/api/probes.py` | `probe`, `magnet` | `Probe`, `Magnet` | lines 57–61, 88, 109, 113, 137 |
| `routes/api/records.py` | `record`, `attachment` | `Record`, `Attachment` | lines 78, 94, 106, 157, 177 |
| `routes/api/servers.py` | `server` | `Server` | lines 68, 79, 100 |
| `routes/api/simulations.py` | `simulation` | `Simulation` | lines 147, 155, 166, 175, 188, 206 |
| `routes/api/sites.py` | `site` | `Site` | lines 89, 97, 111, 132, 149, 161, 174, 203, 228 |
| `routes/api/site_magnets.py` | `site`, `magnet`, `site_magnet` | `Site`, `Magnet`, `SiteMagnet` | lines 26, 29, 54 |
| `routes/api/attachments.py` | `attachment` | `Attachment` | line 15 |
| `routes/api/cad_attachments.py` | `cad_attachment` | `CadAttachment` | lines 17–25, 38 |
| `routes/api/mesh_attachments.py` | `mesh_attachment` | `MeshAttachment` | lines 17–21, 34 |

## Rules

1. **Only** fix the `Model.objects.get(id=...)` + `if not obj:` pattern.
   Do **not** touch:
   - `if not magnet_part.active:` — this tests a method result, not a queryset
   - `if not site_magnet.active:` — same
   - `if not isinstance(...)` — unrelated
   - Any `filter()` or `get_or_create()` call
   - Any logic inside the route bodies beyond the guard

2. The `except` clause must name the correct model's `DoesNotExist`:
   - `Magnet.DoesNotExist`, `Part.DoesNotExist`, `Site.DoesNotExist`, etc.
   - If the model class is not directly available but is accessed via a related
     manager, use the base `ObjectDoesNotExist` from `django.core.exceptions`
     and add the import if not already present.

3. Preserve the existing 404 detail message exactly as written.

4. When two `.get()` calls appear close together (e.g. fetching both `magnet`
   and `part` in `magnet_parts.py`), wrap each individually so the correct
   404 message is returned for each.

## Example — `magnet_parts.py`

```python
# BEFORE
magnet = Magnet.objects.get(id=magnet_id)
if not magnet:
    raise HTTPException(status_code=404, detail="Magnet not found")

part = Part.objects.prefetch_related("magnetpart_set__magnet").get(id=part_id)
if not part:
    raise HTTPException(status_code=404, detail="Part not found")

# AFTER
try:
    magnet = Magnet.objects.get(id=magnet_id)
except Magnet.DoesNotExist:
    raise HTTPException(status_code=404, detail="Magnet not found")

try:
    part = Part.objects.prefetch_related("magnetpart_set__magnet").get(id=part_id)
except Part.DoesNotExist:
    raise HTTPException(status_code=404, detail="Part not found")
```
