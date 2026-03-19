# Part `geometry` Property — Implementation Prompt

## Context

`Part.geometry_config` stores a python_magnetgeo object serialised as JSON (using
`__classname__` format).  Several places in the codebase deserialise it independently
using the same three-step pattern:

```python
config = copy.deepcopy(part.geometry_config)
config["name"] = part.name
obj = unserialize_object(config)
```

This repetition is scattered across `Part.geometry_config_to_json`,
`Part.geometry_config_to_yaml`, and the assembly loops inside
`Magnet.geometry_config_to_json` / `Magnet.geometry_config_to_yaml`.  It means the
name-injection step can be forgotten, `deepcopy` can be omitted accidentally, and
every caller pays the deserialization cost independently.

---

## Goal

Add a `geometry` property to `Part` that returns the live, cached python_magnetgeo
object.  Refactor all downstream consumers to use it.  No schema change is required;
`geometry_config` (JSONField) is unchanged.

---

## Step 1 — Add `Part.geometry` property

File: `python_magnetdb/models/part.py`

Add the following property.  Place it after the existing `allow_modelaxi_file`
property and before `geometry_config_to_json`.

```python
@property
def geometry(self):
    """
    Return the deserialized python_magnetgeo object for this Part, cached
    on the instance.  Returns None if geometry_config is empty.

    The object is of type Helix, Ring, Bitter, CurrentLead, etc. depending
    on Part.type.  Accessing this property on any Part inside a tight loop
    is safe because deserialization only happens once per instance.
    """
    if self.geometry_config is None or self.geometry_config == {}:
        return None
    if not hasattr(self, "_geometry_obj"):
        from python_magnetgeo.deserialize import unserialize_object
        import copy
        config = copy.deepcopy(self.geometry_config)
        config["name"] = self.name
        self._geometry_obj = unserialize_object(config)
    return self._geometry_obj
```

**Important:** `_geometry_obj` is invalidated if `geometry_config` or `name` changes
during the same request.  This is acceptable because Django model instances are not
shared across requests.  If a mutation is needed within a single request (e.g. during
a seed or migration script), call `del part._geometry_obj` to bust the cache.

---

## Step 2 — Simplify `Part.geometry_config_to_json` and `Part.geometry_config_to_yaml`

File: `python_magnetdb/models/part.py`

Replace the existing implementations with one-liners that delegate to `self.geometry`.

```python
@property
def geometry_config_to_json(self):
    """Serialise geometry to JSON string using the python_magnetgeo object."""
    obj = self.geometry
    if obj is None:
        return None
    return obj.to_json()

@property
def geometry_config_to_yaml(self):
    """Serialise geometry to YAML string using the python_magnetgeo object."""
    import yaml
    obj = self.geometry
    if obj is None:
        return None
    return obj.to_yaml()
```

Remove the `import copy`, `import json` and inline `unserialize_object` calls that
were previously in these methods.  Keep the top-level `import copy` only if it is
still used elsewhere in the file.

---

## Step 3 — Simplify the assembly loops in `Magnet`

File: `python_magnetdb/models/magnet.py`

The `geometry_config_to_json` and `geometry_config_to_yaml` methods both contain
per-part assembly loops that manually duplicate the deepcopy/name-inject/unserialize
pattern.  Replace every occurrence of the pattern:

```python
# BEFORE (example from INSERT helix branch)
config = copy.deepcopy(magnet_part.part.geometry_config)
config["name"] = magnet_part.part.name
if "__classname__" not in config:
    config["__classname__"] = "Helix"
helix_obj = unserialize_object(config)
helices.append(helix_obj)
```

with the simpler form:

```python
# AFTER
helices.append(magnet_part.part.geometry)
```

Apply this substitution to every branch (`HELIX`, `RING`, `LEAD`, `BITTER`, `SUPRA`)
in both `geometry_config_to_json` and `geometry_config_to_yaml`.

After the refactor, the only remaining call to `unserialize_object` inside `magnet.py`
should be for `Probe` objects (which do not have a `geometry` property yet — leave
those as-is).

Remove the now-unused `import copy` from `magnet.py` if it is no longer referenced.

---

## Step 4 — Impact on `generate_magnet_directory` action

File: `python_magnetdb/actions/generate_magnet_directory.py`

This action calls `magnet_part.part.geometry_config_to_yaml` directly.  Because Step 2
preserves the same property interface, **no changes are required here**.  Verify the
action still works by running a local test after Step 3.

---

## Step 5 — Impact on the API routes

File: `python_magnetdb/routes/api/parts.py`

The `/api/parts/{id}/geometry.yaml` route calls `part.geometry_config_to_yaml`.  The
interface is unchanged, so **no route changes are required**.

The `PATCH /api/parts/{id}` and `POST /api/parts` routes write to
`part.geometry_config` directly (via `json.loads(geometry_obj.to_json())`).  After
saving, the cached `_geometry_obj` on the instance is stale.  Add a cache bust
immediately after any write to `geometry_config`:

```python
part.geometry_config = json.loads(geometry_obj.to_json())
# Bust the instance-level cache so next access re-deserializes correctly
if hasattr(part, "_geometry_obj"):
    del part._geometry_obj
part.save()
```

Apply this to both the `create` and `update` route handlers.

---

## Step 6 — Impact on seeds

File: `python_magnetdb/seeds/crud.py`

The seed loader calls `part.geometry_config = json.loads(geometry_obj.to_json())`
then `part.save()`.  Apply the same cache bust from Step 5 here for consistency,
even though seeds run in isolation.

---

## Step 7 — Impact on the web frontend (Vue 2.7, current)

File: `web/src/views/parts/show.vue`

The frontend calls `GET /api/parts/{id}/geometry.yaml` on mount and displays the result
in `<GeometryModal>`.  The geometry YAML is already rendered via this dedicated
endpoint — the `Part.geometry_config` JSON field is **never sent raw to the browser**.

No frontend changes are required for correctness.  However, two UX improvements are
worth making while touching this area:

### 7a — Show derived geometry fields in the Part detail view

The `Part.geometry` object exposes type-specific fields that are currently invisible
to users (e.g. for a Helix: `r`, `z`, `cutwidth`, `odd`, `dble`; for a Ring: `r`,
`z`, `n`, `cad`).  Add a new API endpoint to expose a structured summary:

```python
# python_magnetdb/routes/api/parts.py

@router.get("/api/parts/{id}/geometry-summary")
def geometry_summary(id: int, user=Depends(get_user("read"))):
    part = Part.objects.get(id=id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    obj = part.geometry
    if obj is None:
        return {"summary": None}
    # Return the parsed dict directly — already a plain Python dict via to_json()
    import json
    return {"summary": json.loads(obj.to_json())}
```

In `show.vue`, fetch this endpoint alongside the existing YAML fetch and render the
summary as a read-only key-value table beneath the `<GeometryModal>`.  This allows
researchers to see geometry parameters without opening the YAML editor.

### 7b — Show CAD reference field (Ring, Helix model3d/modelaxi)

The `cad`, `model3d.cad`, and `modelaxi.cad` fields from the geometry object are the
fields used by the `find_helix_by_cad.py` migration helper.  Exposing them in the UI
makes it easier to cross-reference the old database.  The `/api/parts/{id}/geometry-summary`
endpoint from 7a already includes these fields; render them prominently when present.

---

## Step 8 — Impact on the React migration (future frontend)

When the Part detail page is built in React (Phase 2 of the frontend migration), the
component should:

1. Fetch `GET /api/parts/{id}` for metadata and attachment references.
2. Fetch `GET /api/parts/{id}/geometry.yaml` for the editable YAML editor
   (Monaco, same as today).
3. Fetch `GET /api/parts/{id}/geometry-summary` (new, from Step 7a) for the
   structured read-only panel.

The three fetches are independent and can be issued in parallel with `Promise.all`.
The geometry summary panel should be conditionally rendered by Part type — show only
the fields relevant to the current type (use a `GEOMETRY_FIELDS_BY_TYPE` map in the
component).

---

## Step 9 — Tests

Update `tests/test_part_simplified.py` and `tests/test_part_geometry_config.py`:

- Add a test that accesses `part.geometry` twice and asserts `unserialize_object` is
  only called once (use `unittest.mock.patch`).
- Add a test that mutates `part.geometry_config`, busts the cache with
  `del part._geometry_obj`, and verifies `part.geometry` reflects the new config.
- Verify `geometry_config_to_json` and `geometry_config_to_yaml` still return the
  same output as before the refactor.

---

## Summary of file changes

| File | Change |
|---|---|
| `python_magnetdb/models/part.py` | Add `geometry` property; simplify `geometry_config_to_json` and `geometry_config_to_yaml` |
| `python_magnetdb/models/magnet.py` | Replace per-part deepcopy/inject/unserialize blocks with `part.geometry` |
| `python_magnetdb/routes/api/parts.py` | Add cache bust after `geometry_config` writes; add `geometry-summary` endpoint |
| `python_magnetdb/seeds/crud.py` | Add cache bust after `geometry_config` write |
| `python_magnetdb/actions/generate_magnet_directory.py` | No change required |
| `web/src/views/parts/show.vue` | Add geometry summary panel (optional, 7a/7b) |
| `tests/test_part_simplified.py` | Add cache and mutation tests |
| `tests/test_part_geometry_config.py` | Add regression tests |

No database migration is required.  The `geometry_config` JSONField schema is
unchanged.
