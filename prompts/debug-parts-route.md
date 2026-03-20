# Debug: `/api/magnets/{id}/parts` returns wrong parts for some magnets

## Context

The route `GET /api/magnets/{id}/parts` in
`python_magnetdb/routes/api/magnets.py` returns the correct number of
`MagnetPart` rows (confirmed by direct SQL), but the serialized `part`
field inside each entry is wrong or `null` for at least one specific magnet.

## What has already been tried / ruled out

1. **Mutable default argument in `model_serializer`** — fixed:
   `already_processed=None` + `if already_processed is None: already_processed = []`
   in `python_magnetdb/routes/api/serializers.py`. Did **not** fix the issue.

2. **Dead-code `if not magnet:` guard** — replaced with `try/except Magnet.DoesNotExist`.
   Unrelated to this bug.

3. **Direct SQL** confirms the correct `part_id` is stored on the `magnet_parts`
   table for the problematic magnet.

## Debug instrumentation already in place

```python
# python_magnetdb/routes/api/magnets.py  — parts()
for part_magnet in magnet.magnetpart_set.all():
    print(f"part_magnet id: {part_magnet.id}, "
          f"part_id (raw): {part_magnet.part_id}, "
          f"part in fields_cache: {'part' in part_magnet._state.fields_cache}")
    serialized = model_serializer(part_magnet)
    print(f"  serialized part: {serialized.get('part')}")
    result.append(serialized)
```

Run `GET /api/magnets/<bad_id>/parts` and share the full server-side output.

## Hypothesis to investigate

The `model_serializer` only serializes a FK relation when
`field.name in model._state.fields_cache` is `True`:

```python
elif field.name in model._state.fields_cache:
    value = getattr(model, field.name)
    if value is not None and value not in already_processed:
        res[field.name] = model_serializer(value, already_processed + [model])
    else:
        res[field.name] = None
```

`prefetch_related("magnetpart_set__part")` populates the prefetch cache but
does **not** necessarily populate `_state.fields_cache` for each
`MagnetPart`'s `part` FK.  If `'part'` is absent from `_state.fields_cache`,
the serializer silently omits it rather than falling back to `part_id`.

### Suggested fix

Replace the FK branch in `model_serializer` to fall back to the `_id` attribute
when the related object is not in the fields cache, or force Django to put the
prefetched FK into the fields cache by accessing `part_magnet.part` once before
calling `model_serializer`.

Option A — access the FK in the route before serializing:

```python
for part_magnet in magnet.magnetpart_set.all():
    _ = part_magnet.part   # force FK into _state.fields_cache
    result.append(model_serializer(part_magnet))
```

Option B — fix `model_serializer` to handle prefetched FKs:

```python
for field in model._meta.fields:
    if not isinstance(field, ForeignKey):
        ...
    else:
        # check both the fields_cache AND the prefetch cache
        if field.name in model._state.fields_cache:
            value = getattr(model, field.name)
        elif hasattr(model, '_prefetched_objects_cache'):
            # prefetch_related on a FK stores it with the attname (e.g. 'part')
            value = model._state.fields_cache.get(field.attname)  # fallback
            value = getattr(model, field.name, None)   # triggers no extra query if prefetched
        else:
            continue
        if value is not None and value not in already_processed:
            res[field.name] = model_serializer(value, already_processed + [model])
        else:
            res[field.name] = None
```

## Files to look at

- `python_magnetdb/routes/api/magnets.py` — `parts()` route
- `python_magnetdb/routes/api/serializers.py` — `model_serializer()`
- `python_magnetdb/models/magnet_part.py` — `MagnetPart` model

## Task

1. Run the debug instrumentation on the problematic magnet and confirm whether
   `'part' in part_magnet._state.fields_cache` is `False`.
2. Apply the appropriate fix so that the `part` object is always serialized
   when it exists, regardless of how Django populated the FK cache.
3. Remove the debug `print` statements once the fix is confirmed.
4. Check all other routes in `magnets.py` that use `if not magnet:` (dead code)
   and apply the same `try/except Magnet.DoesNotExist` pattern.
