# Phase 2 — Core Infrastructure

## Context

MagnetDB React app scaffolded in `web-react/` (Phase 1 complete). This phase implements the
foundational plumbing that every view and component will depend on: auth state, API client,
routing with guards, and the root layout.

These are direct translations of the following Vue 2 files:
- `web/src/store.js` — Vuex store with `token` and `user`
- `web/src/services/client.js` — Axios instance with auth interceptor
- `web/src/router.js` — Vue Router with `beforeEach` auth guard
- `web/src/App.vue` — root layout (topbar, router-view, dropdown)

The backend auth flow: LemonLDAP::NG redirects to `/sign_in?code=xxx`. The frontend exchanges
the code for a token via `POST /api/session`, then stores it. The token is sent as the
`Authorization` header on every subsequent request.

---

## Goal for this phase

Implement auth store, API client, router with protected routes, and root layout. At the end of
this phase the app should render, show the topbar, redirect unauthenticated users to `/sign_in`,
and be ready to receive view components.

---

## Tasks

### 1. Auth store (Zustand)

File: `src/store/auth.ts`

Replaces `web/src/store.js`. Requirements:
- State: `token: string | null`, `user: User | null`
- Actions: `setToken(token)`, `setUser(user)`
- `setToken(null)` must also clear `user`
- Token persisted to localStorage via Zustand `persist` middleware (replaces manual
  `localStorage.setItem` in the Vue store)
- Export a `useAuthStore` hook

Define the `User` type based on the profile view fields: `id`, `username`, `email`, `name`,
`role` (`'guest' | 'user' | 'designer' | 'admin'`), `api_key`.

### 2. API client

File: `src/services/client.ts`

Replaces `web/src/services/client.js`. Requirements:
- Axios instance with `baseURL` from `import.meta.env.VITE_API_ENDPOINT`
- Request interceptor that reads token from `useAuthStore.getState().token` (not from the hook
  — must work outside React components) and sets `Authorization` header
- Export the client as default

### 3. Service modules

Migrate the following service files from `web/src/services/` to `src/services/`, keeping the
same function signatures (they are plain JS/TS, no Vue dependencies):
- `sessionService` — `create({ code, redirect_uri })`, `destroy()`
- `userService` — `find()`, `update({ name })`
- `homeService` — `find()`

These files should be nearly identical to the Vue versions.

### 4. Router

File: `src/router.tsx`

Replaces `web/src/router.js`. Requirements:
- Use `createBrowserRouter` (React Router v6 data API)
- Implement a `<ProtectedRoute>` wrapper component that redirects to `/sign_in` if no token
  (replaces `router.beforeEach`)
- Define all routes from the Vue router, pointing to placeholder components for now:
  - `/sign_in`
  - `/` (home)
  - `/materials`, `/materials/new`, `/materials/:id`, `/materials/:id/edit`
  - `/parts`, `/parts/new`, `/parts/:id`, `/parts/:id/edit`
  - `/magnets`, `/magnets/new`, `/magnets/:id`, `/magnets/:id/edit`
  - `/sites`, `/sites/new`, `/sites/:id`, `/sites/:id/edit`
  - `/simulations`, `/simulations/new`, `/simulations/:id`
  - `/records`, `/records/:id`
  - `/visualisations/bmap`, `/visualisations/bmap_2d`, `/visualisations/stress_map`
  - `/servers`, `/servers/new`, `/servers/:id/edit`
  - `/profile`
  - `/admin/config`, `/admin/users`, `/admin/users/:id`

### 5. Root layout

File: `src/App.tsx`

Replaces `web/src/App.vue`. Requirements:
- Topbar with navigation links (same items as Vue app)
- User dropdown (Welcome, {name} / Profile / Servers / Administrate / Log out)
- "Administrate" link only visible when `user.role === 'admin'`
- `<Outlet />` for the routed content
- On mount: if token exists, fetch current user via `userService.find()` and store with
  `setUser`; on 401, clear token and redirect to `/sign_in`
- Sign out clears token and redirects to `/sign_in`

### 6. Entry point

File: `src/main.tsx`

Wire `RouterProvider` with the router from step 4.

### 7. Tests

Write unit tests for:
- `useAuthStore`: token persistence, user clearing on logout
- `<ProtectedRoute>`: renders children when authenticated, redirects when not
- API client interceptor: token is attached to requests

---

## Constraints

- No Vue dependencies anywhere in `web-react/`
- `useAuthStore.getState()` (not the hook) must be used inside the Axios interceptor
- The `User` type must be defined once and reused across store, services, and components
