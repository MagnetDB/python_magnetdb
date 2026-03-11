# MagnetDB — Site / Magnet / Part Lifecycle Migration Guide

**Version 1.0 · March 2026**  
LNCMI — Laboratoire National des Champs Magnétiques Intenses

---

## 1. Overview

This document describes the implementation plan for the revised lifecycle status model in MagnetDB. The new model introduces a cleaner status set for Sites, Magnets, and Parts, along with a cascading shutdown workflow that correctly propagates status changes down the hierarchy.

The migration is organised into five phases covering backend changes, database migration, API endpoint updates, frontend changes, and validation. Each phase has an estimated effort and a recommended sequencing.

---

## 2. Revised Status Model

### 2.1 Site statuses

| Status | Meaning |
|---|---|
| `in_study` | Site is being designed or evaluated. No magnets are commissioned. |
| `in_operation` | Site is actively running. At least one magnet is in_operation. |
| `stopped` | Site has been shut down. Equipment status is determined by magnet-level outcomes. |

> **Note:** Site never reaches `in_stock`, `retired`, or `defunct`. Its terminal state is always `stopped` — the fate of the equipment is expressed through magnet and part statuses.

### 2.2 Magnet statuses

| Status | Meaning |
|---|---|
| `in_study` | Magnet is being designed. Not yet commissioned into any site. |
| `in_stock` | Design complete. Available for deployment but not currently at any site. |
| `in_operation` | Deployed at an active site. |
| `retired` | Removed from service but physically intact. May be reactivated. At least one part must also be retired. |
| `defunct` | Permanently decommissioned. At least one part must also be defunct. |

### 2.3 Part statuses

| Status | Meaning |
|---|---|
| `in_study` | Part is being designed, attached to an `in_study` magnet. |
| `in_stock` | Part is detached and available. Not bound to any magnet. |
| `in_operation` | Part is bound to a magnet (`in_stock` or `in_operation`). Parts always follow their magnet's operational state. |
| `retired` | Part is retired following its magnet's retirement. May return to `in_stock`. |
| `defunct` | Permanently decommissioned along with its magnet. |

---

## 3. Cascade Rules

### 3.1 put_in_operation (Site → Magnet → Part)

Triggered by `POST /sites/{id}/put_in_operation`.

| Site | Magnet | Part |
|---|---|---|
| `in_study` → `in_operation` | `in_study` or `in_stock` → `in_operation` | `in_study` or `in_stock` → `in_operation` |

> **Important:** `put_in_operation` must accept magnets in either `in_study` or `in_stock`. The current implementation assumes `in_stock` only — this guard must be updated.

### 3.2 shutdown (Site → Magnet → Part)

Triggered by `POST /sites/{id}/shutdown`. The site always becomes `stopped`. Each active magnet is explicitly assigned a target status in the request payload.

| Magnet assignment | Selected parts | Remaining parts |
|---|---|---|
| `in_stock` | — (not applicable) | `in_operation` (unchanged) |
| `retired` | `retired` (≥1 required) | `in_stock` |
| `defunct` | `defunct` (≥1 required) | `in_stock` |

> **Note:** Parts always remain `in_operation` when their magnet returns to `in_stock`. They are only individually assessed when the magnet reaches a terminal state (`retired` or `defunct`).

### 3.3 Shutdown from in_study site

If a site is shut down before ever being commissioned (still `in_study`), no cascade occurs. Magnets and parts remain `in_study`. Only the site transitions to `stopped`.

### 3.4 Standalone magnet endpoints

In addition to site-driven transitions, two direct magnet endpoints allow terminal status assignment without a site shutdown:

- `POST /magnets/{id}/retire` — magnet → `retired`, ≥1 part → `retired`, rest → `in_stock`
- `POST /magnets/{id}/defunct` — magnet → `defunct`, ≥1 part → `defunct`, rest → `in_stock`

---

## 4. Shutdown API Payload

The revised shutdown endpoint accepts a structured JSON body. Every active magnet on the site must appear in the payload — there are no implicit defaults.

```json
{
  "decommissioned_at": "2025-03-01T00:00:00Z",
  "magnets": [
    { "magnet_id": 1, "status": "in_stock" },
    {
      "magnet_id": 2,
      "status": "retired",
      "parts": [{ "part_id": 45, "status": "retired" }]
    },
    {
      "magnet_id": 3,
      "status": "defunct",
      "parts": [{ "part_id": 67, "status": "defunct" }]
    }
  ]
}
```

**Validation rules enforced before any write:**

- All active magnet IDs on the site must be present in the payload
- Each magnet status must be one of: `in_stock`, `retired`, `defunct`
- For `retired` magnets, at least one part must have status `retired`
- For `defunct` magnets, at least one part must have status `defunct`
- All referenced part IDs must be active parts belonging to the named magnet
- The entire operation executes inside `transaction.atomic()` — all or nothing

---

## 5. Implementation Phases

### Phase 1 — Backend Model & Database · ~0.5 day

#### 1.1 Add RETIRED and STOPPED to Status

File: `python_magnetdb/models/status.py`

- Add `RETIRED = 'retired'`
- Add `STOPPED = 'stopped'`
- `DEFUNCT` remains; `IN_STOCK`, `IN_STUDY`, `IN_OPERATION` unchanged

#### 1.2 Django migration

Generate a new migration that adds `'retired'` and `'stopped'` to the `choices` field on `Site.status`, `Magnet.status`, and `Part.status`. No data migration is needed at this stage — existing rows keep their current values.

- Run: `python manage.py makemigrations`
- Review the generated file to confirm only `choices` are altered
- Run: `python manage.py migrate` in a test environment

> **Warning:** Do not rename or remove existing status values (`in_stock`, `defunct`, etc.) in this migration. Existing data must remain valid throughout the migration window.

---

### Phase 2 — API Endpoint Updates · ~1 day

#### 2.1 POST /sites/{id}/shutdown — rewrite

Replace the current endpoint with the new payload-driven implementation:

- Accept a Pydantic `ShutdownPayload` model with the JSON structure from Section 4
- Run validation before any DB writes (all active magnets present, part constraints)
- Wrap execution in `transaction.atomic()`
- Site → `stopped`
- Each magnet: apply assigned status, set `SiteMagnet.decommissioned_at`
- For `retired`/`defunct` magnets: apply status to selected parts, `in_stock` to remainder
- For `in_stock` magnets: parts remain `in_operation`

#### 2.2 POST /sites/{id}/put_in_operation — guard update

The current implementation assumes magnets are `in_stock` before commissioning. Update the guard to also accept `in_study` magnets:

- Accept `magnet.status` in `{in_study, in_stock}` — reject any other status
- Parts in `in_study` or `in_stock` → `in_operation`

#### 2.3 POST /magnets/{id}/retire — new endpoint

New standalone endpoint mirroring the existing `/magnets/{id}/defunct` pattern:

- Accept `retired_parts` list in the request body (at least one required)
- Validate all part IDs are active parts of this magnet
- Selected parts → `retired`, remainder → `in_stock`
- Magnet → `retired`
- Set `MagnetPart.decommissioned_at` for active links

#### 2.4 POST /magnets/{id}/defunct — update

Align the existing endpoint to the new part rules:

- Currently sets all parts to `in_stock` indiscriminately
- Update to accept `defunct_parts` list (at least one required)
- Selected parts → `defunct`, remainder → `in_stock`

---

### Phase 3 — Frontend: Status Display · ~0.5 day

#### 3.1 StatusBadge component

Add `retired` and `stopped` to the badge colour mapping:

- `stopped` → amber / warning style (same visual weight as `in_progress`)
- `retired` → neutral amber, distinct from both `in_stock` (blue) and `defunct` (red)

#### 3.2 Status label filter

In `main.js` (Vue) and the equivalent React utility:

- Add `stopped: 'Stopped'`
- Add `retired: 'Retired'`

#### 3.3 Site list / detail views

Replace any hardcoded `defunct` references in filter dropdowns, table columns, and detail headers with the full updated status set.

---

### Phase 4 — Frontend: Shutdown Workflow · ~2 days

The shutdown UX requires a multi-step dialog to collect the per-magnet decisions. This is the most significant frontend change.

#### 4.1 Shutdown dialog — step 1

Display all active magnets attached to the site. For each magnet, provide a status selector: `in_stock` / `retired` / `defunct`.

#### 4.2 Shutdown dialog — step 2

For each magnet assigned `retired` or `defunct`, display that magnet's active parts. Allow the user to select which parts share the terminal status; the rest are implicitly `in_stock`.

Enforce the ≥1 part selection constraint in the UI before the submit button is enabled.

#### 4.3 Confirmation and submission

Show a summary of all decisions before submitting. On confirmation, POST the structured payload to `/sites/{id}/shutdown`.

#### 4.4 Reactivation (retired → in_stock)

Add a **Reactivate** action to the magnet detail view when status is `retired`. This transitions the magnet back to `in_stock` and its parts back to `in_operation`. A simple confirmation dialog is sufficient — no part selection needed.

---

### Phase 5 — Testing & Data Validation · ~1 day

#### 5.1 Backend unit tests

- Test each valid status transition for Site, Magnet, Part
- Test cascade correctness: `put_in_operation`, normal shutdown, `retired` shutdown, `defunct` shutdown
- Test validation errors: missing magnets in payload, zero parts selected for `retired`/`defunct`
- Test shutdown from `in_study` site (no cascade)
- Test transaction rollback on validation failure

#### 5.2 Existing data audit

Before deploying, run a query to audit existing status values against the new rules:

- Any site marked `defunct` should be reviewed — does it map to `stopped`?
- Confirm no magnets are in a status that would be invalid under the new model
- If a data migration is needed, prepare and review it separately before applying

> **Warning:** The `DEFUNCT` site status in existing data will not automatically become `STOPPED`. If the site status column must be normalised, a separate targeted data migration is required after Phase 1.

#### 5.3 Integration test in staging

- Full shutdown workflow with mixed magnet outcomes (`in_stock` + `retired` + `defunct` in one call)
- Verify `SiteMagnet.decommissioned_at` and `MagnetPart.decommissioned_at` are set correctly
- Verify reactivation path (`retired` magnet → `in_stock`)

---

## 6. Effort Summary

| # | Phase | Scope | Estimate |
|---|---|---|---|
| 1 | Backend Model & Database | `status.py`, migration | 0.5 day |
| 2 | API Endpoint Updates | `sites.py`, `magnets.py`, Pydantic models | 1 day |
| 3 | Frontend — Status Display | `StatusBadge`, filters, list views | 0.5 day |
| 4 | Frontend — Shutdown Workflow | Multi-step dialog, reactivation | 2 days |
| 5 | Testing & Data Validation | Unit tests, data audit, integration | 1 day |
| | **Total** | | **~5 days** |

Phases 1 and 2 must be completed and deployed before Phases 3 and 4 begin. Phases 3 and 4 can proceed in parallel if two developers are available.

---

## 7. Files Affected

| File | Change |
|---|---|
| `python_magnetdb/models/status.py` | Add `RETIRED`, `STOPPED` constants |
| `python_magnetdb/migrations/XXXX_*.py` | Add choices for new statuses on Site, Magnet, Part |
| `python_magnetdb/routes/api/sites.py` | Rewrite `shutdown`, update `put_in_operation` guard |
| `python_magnetdb/routes/api/magnets.py` | Add `/retire` endpoint, update `/defunct` part logic |
| `web/src/components/StatusBadge.vue` | Add `retired`, `stopped` badge styles |
| `web/src/main.js` | Add `retired`, `stopped` to `statusName` filter |
| `web/src/views/Sites/*` | New multi-step shutdown workflow component |
| `web/src/views/Magnets/*` | Add retire action and reactivation button |
