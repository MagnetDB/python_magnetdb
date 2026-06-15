# Phase 3 — Browser Smoke Test Procedure

Validates the `vue-reactive-provide` → `setup() + provide(reactive(...))` replacement
and all associated `$listeners` / `$scopedSlots` fixes, without Docker or a real backend.

---

## Prerequisites

- Phase 1 (Vite tooling) and Phase 2 (Vue 3 core upgrade) complete
- Phase 3 changes applied (`Form.vue`, `FormValues.vue`, `Button.vue`, `DataTable.vue`)

---

## Step 1 — Start the dev server

```bash
source /home/LNCMI-G/christophe.trophime/github/python_magnetdb/.venv/bin/activate
cd web
npm run dev
```

Server listens on `http://localhost:8080`.
The app immediately redirects to `/sign_in` (no real token yet).

---

## Step 2 — Bypass auth

Open `http://localhost:8080/sign_in` in the browser.
Open DevTools → **Console** tab and run:

```js
localStorage.setItem('magnetdb_session_token', 'fake-token')
```

The router guard reads `localStorage` directly, so this is enough to pass it.
No page reload needed — just navigate manually to the test URLs below.

---

## Step 3 — Check the Console baseline

Before navigating anywhere, verify the Console is clean.
Vue 3 migration warnings to watch for:

| Warning text | Root cause |
|---|---|
| `[Vue warn]: Property "$listeners" was accessed` | missed `$listeners` reference |
| `[Vue warn]: $scopedSlots is removed` | missed `$scopedSlots` reference |
| `[Vue warn]: Unknown custom element option "reactiveProvide"` | old plugin option still present |
| `[Vue warn]: inject() can only be used inside setup()` | provide/inject wiring broken |

**Expected:** zero warnings before any navigation.

---

## Step 4 — `Form.vue` + `Button.vue` → `/materials/new`

Navigate to `http://localhost:8080/materials/new`.

### Checks

| # | What to do | Expected result | What it proves |
|---|---|---|---|
| 4.1 | Page loads | All input fields render, no blank page, no console errors | `provide(reactive(...))` wires up correctly |
| 4.2 | Observe Save button on load | Button is dimmed / unclickable | `form.dirty` starts `false` and is reactive via `inject` |
| 4.3 | Type anything in the **Name** field | Save button becomes active | `form.values` mutation propagates reactively to `Button.vue` |
| 4.4 | Clear Name, click Save | Validation error appears **under the Name field** (not a network error) | `attrs.onValidate` is called correctly from `Form.vue`'s `submit()` |
| 4.5 | Fill in Name, click Save | Red alert appears **above the form** (401 from API) | `attrs.onSubmit` is called; `setRootError` path works |
| 4.6 | Observe Save button while request is in flight | Spinner shown on button | `form.loading` is reactive |

---

## Step 5 — `DataTable.vue` → `/materials`

Navigate to `http://localhost:8080/materials`.

### Checks

| # | What to do | Expected result | What it proves |
|---|---|---|---|
| 5.1 | Open DevTools → **Network** tab, then navigate | A request to `/api/materials` is made | `$attrs.onFetch` is called on mount |
| 5.2 | Observe the page | Error alert shown instead of table, no JS exception in Console | Error handling path in `fetch()` works |

---

## Step 6 — `FormValues.vue` → `/parts/1`

Navigate to `http://localhost:8080/parts/1`.

The API call for part #1 will 401 — that is expected.

### Checks

| # | What to do | Expected result | What it proves |
|---|---|---|---|
| 6.1 | Page loads | Error state rendered, **no JS exception** in Console | `$slots.default(...)` call doesn't crash (would throw if `$scopedSlots` was still used) |

---

## What cannot be validated without Docker

These items require a real backend and belong to **Phase 7 (integration testing)**:

- Successful form submission (needs real API response)
- DataTable row rendering and `onItemSelected` cursor class (needs real data)
- `FormValues` scoped slot content (needs a real part record to load)

---

## Pass criteria

- [ ] No Vue 3 migration warnings in the Console at any point
- [ ] 4.1 — form renders
- [ ] 4.2 — button disabled on load
- [ ] 4.3 — button enables after typing
- [ ] 4.4 — client-side validation error appears under the field
- [ ] 4.5 — API error surfaces as root alert above the form
- [ ] 4.6 — button shows loading spinner during request
- [ ] 5.1 — `/api/materials` network request is made
- [ ] 5.2 — error alert shown, no JS exception
- [ ] 6.1 — `/parts/1` renders error state without JS exception
