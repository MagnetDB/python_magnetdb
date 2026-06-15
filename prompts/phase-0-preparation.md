# Phase 0 — Preparation & Audit

## Context

MagnetDB is a scientific data platform for magnet design and experimental analysis developed at
LNCMI. The frontend is currently **Vue.js 2.7** (EOL) with Webpack, Vuex, Vue Router 3, and
Tailwind CSS. The goal is to migrate to **React + Vite + Vitest** incrementally, without breaking
the existing app during the transition.

**Backend**: Django / FastAPI, PostgreSQL, Celery/Redis — untouched by this migration.  
**Auth**: LemonLDAP::NG SSO with token stored in localStorage.  
**Visualization**: Chart.js (dashboard), Plotly.js (scientific plots), Monaco Editor
(simulation config), vtk.js planned for CAD/mesh.

Relevant source files:
- `web/src/store.js` — Vuex store (token + user)
- `web/src/router.js` — Vue Router with auth guard
- `web/src/services/client.js` — Axios client with auth interceptor
- `web/src/App.vue` — root layout with topbar and router-view
- `web/src/views/` — one `.vue` file per route
- `web/src/components/` — shared components (Form, DataTable, Card, etc.)

---

## Goal for this phase

Produce a **complete inventory and migration map** before writing any React code. This phase is
purely analytical — no new files, no new dependencies.

---

## Tasks

### 1. Component inventory

List every file under `web/src/components/` and `web/src/views/` with:
- Its purpose (one line)
- Complexity rating (low / medium / high)
- Dependencies on Vue-specific APIs (`$store`, `$router`, `$route`, `$refs`, filters, mixins)
- External libraries used (Chart.js, Plotly, Monaco, etc.)
- Suggested React equivalent or migration strategy

### 2. Service layer inventory

List every file under `web/src/services/` with:
- API endpoints it calls
- Whether it needs changes for the React app (usually none — pure JS)

### 3. Vue-to-React mapping table

Produce a reference table covering:

| Vue 2 concept | React equivalent |
|---|---|
| `data()` | `useState` |
| `computed` | `useMemo` |
| `methods` | functions / custom hooks |
| `mounted` | `useEffect(() => {}, [])` |
| `watch` | `useEffect` with dependencies |
| `$store.state.x` | `useAuthStore(s => s.x)` (Zustand) |
| `$store.commit(...)` | store action from Zustand |
| `$router.push(...)` | `useNavigate()` |
| `$route.params.id` | `useParams()` |
| Vue filters (`\| datetime`) | utility functions |
| `v-if` / `v-show` | conditional JSX |
| `v-for` | `.map()` in JSX |
| `v-model` | controlled input + `onChange` |
| `@submit` / `@click` | `onSubmit` / `onClick` |
| `<slot>` | `children` prop |
| Named slots | render props or component props |
| Mixins | custom hooks |

### 4. Migration order

Propose a migration order for views from simplest to most complex, taking into account:
- State complexity
- Number of sub-components
- Use of WebSockets (simulation streaming = most complex)
- Use of external visualization libs

### 5. Environment variables

List all `VUE_APP_*` variables from the codebase and their `VITE_*` equivalents.

---

## Constraints

- The Vue 2 app must remain fully functional throughout the migration
- The React app will live in a new `web-react/` directory alongside `web/`
- No shared build pipeline between old and new app during migration
- Tailwind CSS classes are reused as-is (no redesign in scope)
