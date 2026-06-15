# Phase 1 — Scaffold the React App (Vite + Vitest)

## Context

MagnetDB frontend migration from Vue 2.7 to React. The Vue app lives in `web/`. The new React
app will be built in `web-react/` and will eventually replace it entirely. The backend
(Django/FastAPI) is unchanged. Docker + Traefik handle SSL and routing.

**Target stack:**
- React 18 + TypeScript
- Vite (build tool, dev server)
- Vitest + Testing Library (unit/integration tests)
- React Router v6 (routing)
- Zustand (global state — replaces Vuex)
- React Hook Form + Yup (forms — Yup already used in Vue app)
- Axios (HTTP client — reused from Vue app)
- Tailwind CSS (reused as-is)

---

## Goal for this phase

Bootstrap a working, empty React app with all tooling configured and verified. No business logic
yet — just a solid, runnable foundation.

---

## Tasks

### 1. Project creation

Create the app using Vite:

```bash
npm create vite@latest web-react -- --template react-ts
```

Install all dependencies listed above.

### 2. Vite configuration

Configure `vite.config.ts` with:
- React plugin
- Vitest test environment (`jsdom`)
- Path alias `@/` pointing to `src/`
- Dev server proxy to backend (`/api` → `http://localhost:8000`) to avoid CORS issues in dev

### 3. Vitest configuration

In `vite.config.ts`:
- `environment: 'jsdom'`
- `globals: true` (so tests don't need to import `describe`/`it`/`expect`)
- `setupFiles: ['./src/test-setup.ts']`

Create `src/test-setup.ts` that imports `@testing-library/jest-dom`.

Write a minimal smoke test to verify the setup works.

### 4. Tailwind CSS

Set up Tailwind using the same config as the Vue app (`web/tailwind.config.js`) to ensure
visual consistency during the parallel-running phase.

### 5. Environment variables

Create `.env.development` with:
```
VITE_API_ENDPOINT=http://localhost:8000
```

Document the rename from `VUE_APP_*` to `VITE_*`.

### 6. Project structure

Scaffold the following directory layout:

```
web-react/
  src/
    components/       # shared UI components
    views/            # one file per route (mirrors web/src/views/)
    services/         # API service modules (mirrors web/src/services/)
    store/            # Zustand stores
    hooks/            # custom React hooks
    utils/            # filters, formatters, helpers
    router.tsx        # React Router config
    App.tsx           # root component
    main.tsx          # entry point
    test-setup.ts
  public/
  vite.config.ts
  tsconfig.json
  tailwind.config.js
  .env.development
```

### 7. Docker integration

Update `docker-compose.yml` to add a `frontend-react` service that:
- Runs `npm run dev` in `web-react/`
- Mounts source for HMR
- Is accessible at a different port (e.g. `3001`) during parallel-running phase
- Is **not** yet connected to Traefik (Vue app keeps its routes)

### 8. Verification checklist

- [ ] `npm run dev` starts with no errors
- [ ] `npm run build` produces a dist without errors
- [ ] `npm run test` runs and the smoke test passes
- [ ] Path alias `@/` resolves correctly
- [ ] Tailwind classes render correctly on a test component
- [ ] API proxy forwards `/api` requests to Django

---

## Constraints

- TypeScript is required from day one (not optional)
- No UI component library (shadcn/ui may be introduced later for complex components)
- `eslint` + `prettier` must be configured consistent with the existing codebase style
