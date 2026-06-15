# Migration Plan: Vue 2 + Webpack → Vue 3 + Vite

**Date:** 2026-05-10
**Branch base:** `node22` (must be stable/merged first)
**Scope:** `web/` frontend only

---

## Current Stack

- Vue 2.7.16 + Vue CLI 5 (Webpack 5)
- Vuex 3, Vue Router 3
- 66 `.vue` components, 23 `.js` modules
- 1 mixin (`createFormField.js`), ~15 service files
- Key third-party UI libs: `vue-select` v3, `@vue-hero-icons/outline|solid`, `vue-reactive-provide`

---

## Breaking Changes Inventory

| Category | Items affected | Complexity |
|---|---|---|
| **Entry point** (`main.js`) | `new Vue()` → `createApp()`, `Vue.use()` → `app.use()`, `Vue.prototype.$x` → `app.config.globalProperties` | Low |
| **Vuex 3 → Vuex 4** | `new Vuex.Store()` → `createStore()` in `store.js`; API mostly compatible | Low |
| **Vue Router 3 → 4** | `new VueRouter()` → `createRouter()`, `mode: 'history'` → `createWebHistory()` in `router.js` | Low |
| **`vue-reactive-provide`** | Plugin dropped (incompatible with Vue 3). `Form.vue` uses `reactiveProvide:` — must be replaced with Vue 3 native `provide()` + `reactive()` in Composition API | Medium |
| **`$filters` global** | `Vue.prototype.$filters = filters` + `$filters.datetime/statusName/roleName` calls in ~20 files — Vue 3 removed `$filters`; replace with composable or `app.config.globalProperties` | Medium |
| **`vue-select` v3** | Vue 2 only. Must upgrade to `vue-select@beta` (v4 Vue 3 port) or replace with an alternative (`vue3-select-component`, Headless UI Combobox) | Medium |
| **`@vue-hero-icons/outline` / `solid`** | Vue 2 packages; must switch to `@heroicons/vue` (official Vue 3 package) | Low |
| **`vue-template-compiler`** | Dev dependency only — removed entirely (not needed in Vue 3) | Trivial |
| **`VueMonacoEditorPlugin`** | `@guolao/vue-monaco-editor` supports Vue 3 — install syntax changes to `app.use()`, otherwise compatible | Low |
| **`inject` in components/mixin** | `Button.vue`, `Form*.vue`, `CurrentsField.vue`, `createFormField` mixin all use `inject: ['form']` — works unchanged in Vue 3 Options API | None |
| **Webpack → Vite** | Replace `vue.config.js` + `babel.config.js` with `vite.config.js`; remove `@vue/cli-*` devDeps; add `@vitejs/plugin-vue`; fix `stream`/`assert` stubs | Low–Medium |

---

## Phase Breakdown & Effort

### Phase 1 — Tooling swap (Webpack → Vite) · ~4–6 h

- Remove `@vue/cli-service`, `@vue/cli-plugin-babel`, `@vue/cli-plugin-eslint`
- Add `vite`, `@vitejs/plugin-vue`; keep `eslint-plugin-vue` v10 (already present)
- Write `vite.config.js`:
  - Dev server with `allowedHosts` (replace `vue.config.js` devServer block)
  - `define: { global: 'globalThis' }` to replace Node global stubs
  - `resolve.alias` for `stream` / `assert` stubs (replacing Webpack `resolve.fallback`)
- Replace `public/index.html` entrypoint with Vite-style root `index.html` + `<script type="module" src="/src/main.js">`
- Update `package.json` scripts: `"dev": "vite"`, `"build": "vite build"`, `"preview": "vite preview"`
- Remove `babel.config.js` (Vite uses esbuild; Babel not needed for Vue 3 SFCs)
- Update Dockerfiles (remove any lingering `NODE_OPTIONS` env vars; adjust build command)
- **Validation:** `vite build` exits 0; `vite dev` starts; app shell loads in browser

---

### Phase 2 — Core Vue upgrade · ~3–4 h

- `npm install vue@^3 vuex@^4 vue-router@^4`
- Remove `vue-template-compiler` from dependencies
- Rewrite `store.js`:
  ```js
  import { createStore } from 'vuex'
  export default createStore({ ... })
  ```
- Rewrite `router.js`:
  ```js
  import { createRouter, createWebHistory } from 'vue-router'
  export default createRouter({ history: createWebHistory(), routes: [...] })
  ```
- Rewrite `main.js` entrypoint:
  ```js
  import { createApp } from 'vue'
  const app = createApp(App)
  app.use(store).use(router).use(VueMonacoEditorPlugin, { ... })
  app.config.globalProperties.$filters = filters
  app.mount('#app')
  ```
- **Validation:** App boots; routing works; Vuex store state persists across navigation; auth token flow intact

---

### Phase 3 — `vue-reactive-provide` replacement · ~4–6 h

This is the **highest-risk change**. `Form.vue` is the root of the form system
used across all CRUD views.

- `Form.vue`: remove `reactiveProvide:` option; replace with Composition API:
  ```js
  import { provide, reactive } from 'vue'
  setup() {
    const form = reactive({ values: {}, errors: {}, setValues, ... })
    provide('form', form)
  }
  ```
- Verify all `inject: ['form']` consumers (`FormInput`, `FormSelect`, `FormSlider`,
  `FormUpload`, `FormValues`, `FormInputWithUnit`, `Button`, `CurrentsField`,
  `createFormField` mixin) still receive a reactive reference
- `vue-reactive-provide` can be replaced without touching any consumer component
  since they already use standard `inject`
- **Validation:** All CRUD forms (magnets, parts, sites, simulations, materials, records)
  submit correctly; validation errors display on the correct fields; form reset works

---

### Phase 4 — Unit tests · ~2–3 h

Set up the test infrastructure and write targeted unit tests before continuing with
further component changes. Phase 3 (`Form.vue`) is the highest-risk change; tests
here both cover that work and serve as a safety net for Phases 5 and beyond.

#### 4.1 — Test runner setup

Install:
```bash
npm install --save-dev vitest @vue/test-utils jsdom @vitest/coverage-v8
```

Add to `vite.config.mjs`:
```js
test: {
  environment: 'jsdom',
  globals: true,
  setupFiles: ['./src/test-setup.js'],
}
```

Create `src/test-setup.js`:
```js
import { config } from '@vue/test-utils'
// global stubs / matchers can go here
```

Add scripts to `package.json`:
```json
"test": "vitest run",
"test:watch": "vitest",
"test:coverage": "vitest run --coverage"
```

#### 4.2 — Store unit tests (`src/store.js`)

File: `src/__tests__/store.spec.js`

- `setToken(token)` persists to `localStorage` and sets `state.token`
- `setToken(null)` removes from `localStorage`, clears `state.token` and `state.user`
- `isLogged` getter returns `true` when token is set, `false` when null
- Store initialises `token` from `localStorage` on creation

#### 4.3 — Router guard unit tests (`src/router.js`)

File: `src/__tests__/router.spec.js`

- Unauthenticated user navigating to any protected route is redirected to `/sign_in`
- Authenticated user navigating to any protected route proceeds normally
- Navigating to `/sign_in` always proceeds regardless of auth state

Use `createMemoryHistory()` (no DOM needed) and a fresh store per test to avoid
state leakage.

#### 4.4 — Form system unit tests (`src/components/Form.vue`)

This is the highest-value test target — `Form.vue` provides reactive state to ~10
consumer components and any reactivity regression breaks all CRUD views silently.

File: `src/__tests__/Form.spec.js`

- `provide`d `form` object is reactive: a consumer that injects `form` sees updated
  `values` and `errors` without re-mounting
- `setValues(patch)` merges values correctly
- Validation errors set on `form.errors` are visible to injected consumers
- Form reset clears `values` and `errors`

Use `@vue/test-utils` `mount` with a minimal consumer stub component that calls
`inject('form')` to verify reactivity end-to-end.

#### 4.5 — Validation checklist

- [x] `npm run test` exits 0
- [x] All three test suites (store, router, Form) pass — 19 tests total
- [x] `npm run test:coverage` shows meaningful coverage on the changed files — Form.vue 87.9% statements, store/router fully covered via inline rebuild

---

### Phase 5 — `$filters` → globalProperties or composable · ~2–3 h

Two equivalent approaches:

**Option A (minimal changes):** Register on `app.config.globalProperties`:
```js
// main.js — already planned in Phase 2
app.config.globalProperties.$filters = filters
```
No template changes needed — `$filters.datetime(...)` calls continue to work.

**Option B (idiomatic Vue 3):** Create `src/composables/useFilters.js` and
import in each component. More boilerplate but more testable.

Recommended: **Option A** first (zero template changes), refactor to composable later.

Affected files (~20): `StatusBadge.vue`, `servers/list.vue`, `admin/audit-logs.vue`,
`admin/users/list.vue`, `records/list.vue`, `sites/list.vue`, `simulations/list.vue`,
`materials/list.vue`, `parts/list.vue`, `magnets/list.vue`, `magnets/show/index.vue`.

- **Validation:** Timestamps and status/role labels render correctly in all list views

---

### Phase 6 — Third-party Vue 2 package replacements · ~4–8 h

#### `vue-select` v3 → v4

`vue-select@beta` is the Vue 3 port. Key API differences:
- Some prop and slot names changed — audit `FormSelect.vue` against v4 changelog
- CSS import path may change
- Alternative: replace with `vue3-select-component` or Headless UI `Combobox`

#### `@vue-hero-icons/outline` / `@vue-hero-icons/solid` → `@heroicons/vue`

```
npm uninstall @vue-hero-icons/outline @vue-hero-icons/solid
npm install @heroicons/vue
```

Import syntax changes:
```js
// Before
import { BeakerIcon } from '@vue-hero-icons/outline'
// After
import { BeakerIcon } from '@heroicons/vue/24/outline'
```

Find all icon imports: `grep -r "@vue-hero-icons" src/`

- **Validation:** All dropdowns filter correctly; all icons render at correct size/style

---

### Phase 7 — Integration testing & regression · ~4–8 h

Manual walkthrough of all major flows:

| Flow | What to verify |
|---|---|
| Sign-in / sign-out | Auth token stored in localStorage; store state correct |
| Sites CRUD | List, create, show, attach magnet modal |
| Magnets CRUD | List, create, show, add part modal |
| Parts CRUD | List, create, show |
| Materials CRUD | List, create, show |
| Records | List, create, show, visualisation card, chart.js plots |
| Simulations | List, new (with currents field), commissioning flow, show, run modal, measures card |
| Probes | Show page with plotly.js visualisation |
| Visualisations | `bmap.vue`, `bmap-2d.vue`, `stress-map.vue` |
| Admin | Config, audit logs, users list/show |
| Monaco editor | Code blocks render and are editable |
| File uploads | CAD attachment, mesh attachment editors |

Also check browser console for Vue 3 migration warnings:
- `$listeners` is merged into `$attrs` in Vue 3 — any explicit `$listeners` usage will warn
- `v-model` argument syntax changed for custom components
- `key` on `<template v-for>` moved to the `<template>` tag

---

## Total Estimate

| Scenario | Hours |
|---|---|
| Best case (no surprises) | 19–24 h |
| Likely | 24–31 h |
| With unknowns / rework | 32–38 h |

---

## Risk Factors

1. **`vue-reactive-provide` / `Form.vue`** — central to the form system; any
   reactivity regression will break all CRUD views simultaneously
2. **`vue-select` v4 API compatibility** — beta package, changelog gaps; may
   need a full replacement component
3. **plotly.js / chart.js** — both support Vue 3 independently (not Vue-wrapped),
   so risk is low but visualisation pages should be verified end-to-end
4. **Vite `stream`/`assert` stubs** — already handled in Webpack 5 fallbacks;
   Vite approach is different but straightforward

## Prerequisites

### node22 branch

The `node22` branch must be fully merged and stable before starting this migration,
since Vite requires Node ≥ 18 and the `--openssl-legacy-provider` workaround
must already be removed (which it is on `node22`).

### Development environment (Phases 1–5)

Phases 1–5 are pure frontend work — no backend required. Use a **nodeenv** virtual
environment for fast iteration (no Docker overhead, native Vite HMR).

```bash
# One-time setup
pip install nodeenv
nodeenv --node=22.15.0 ~/.local/share/nodeenvs/magnetdb-vue3

# Activate before working
source ~/.local/share/nodeenvs/magnetdb-vue3/bin/activate

# Install frontend dependencies
cd web
npm install
```

Typical workflow:

```bash
# Start dev server (after Phase 1 tooling swap)
npm run dev          # vite

# Build check
npm run build        # vite build

# Lint
npm run lint

# Deactivate when done
deactivate
```

> **Phase 6 (integration testing):** switch to Docker Compose (`docker-compose-dev-traefik-ssl.yml`)
> to validate auth flows, API proxying via Traefik, and the full CRUD + visualisation stack.
