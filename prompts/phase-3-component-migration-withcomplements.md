# Phase 3 — Component & View Migration

## Context

MagnetDB React app with core infrastructure in place (Phase 2 complete): Zustand auth store,
Axios client, React Router v6, and root layout all working. This phase migrates shared
components and views one by one, replacing placeholder routes with real implementations.

Vue source files live in `web/src/`. React targets go in `web-react/src/`. The backends
(Django/FastAPI REST endpoints) are unchanged.

**Key Vue → React translation patterns** (established in Phase 0):

| Vue 2 | React |
|---|---|
| `data()` | `useState` |
| `computed` | `useMemo` / derived state |
| `mounted` | `useEffect(() => {}, [])` |
| `watch` | `useEffect` with deps |
| `methods` | functions or custom hooks |
| `$store.state.token` | `useAuthStore(s => s.token)` |
| `$router.push(...)` | `useNavigate()` |
| `$route.params.id` | `useParams()` |
| Vue filter `\| datetime` | `utils/formatters.ts` function |
| `<slot>` | `children` |
| Named slots | explicit props / render props |
| `v-model` on input | `value` + `onChange` |

**Form stack**: React Hook Form + Yup (Yup schemas already exist in Vue app).  
**Tables**: TanStack Table v8 (replaces custom `DataTable` component).  
**Charts**: `react-chartjs-2` wrapper (dashboard) + Plotly.js kept as-is.

---

## Migration order

Migrate in this order (simplest → most complex):

1. Shared UI components (no business logic)
2. `sign_in` view
3. `home` dashboard
4. CRUD views: Materials → Parts → Magnets → Sites (repetitive pattern, build it once right)
5. Records views
6. Servers views
7. Profile view
8. Admin views
9. Simulation views (most complex — WebSocket streaming)
10. Visualisation views (Plotly, bmap, stress map)

---

## ⚠️ Decision required before starting this phase

**shadcn/ui — use it or not?**

This decision must be made before writing any component code, as it affects the
implementation approach for several components below.

shadcn/ui is a **copy-paste component library** (not a runtime dependency) built on
[Radix UI](https://www.radix-ui.com/) primitives. Components are generated into
`src/components/ui/` and owned by the project. Install with:

```bash
npx shadcn@latest init
npx shadcn@latest add dialog popover combobox
```

**Option A — Use shadcn/ui (recommended for complex primitives only)**

Replace the following custom Vue components with their shadcn equivalents:

| Vue component | shadcn component | Why |
|---|---|---|
| `Modal` | `Dialog` | Focus trapping, keyboard nav, ARIA roles — hard to get right from scratch |
| `Popover` | `Popover` | Used on simulation list; same accessibility concerns |
| `FormSelect` with `@search` | `Combobox` | Async search with keyboard navigation is non-trivial |

All other components (`Card`, `Button`, `Alert`, `StatusBadge`, `FormInput`, `FormField`)
are simple enough to rewrite directly in Tailwind — shadcn adds no meaningful value there.

**Option B — No shadcn/ui**

Implement all components from scratch with Tailwind. Acceptable if you want zero external
UI dependencies, but plan extra time for `Modal` and `Popover` to handle accessibility
correctly (focus trapping via `focus-trap-react`, keyboard events, scroll lock).

**Impact on the rest of this prompt:** tasks marked `[shadcn]` below have two sub-options
depending on this choice. All other tasks are unaffected.

---

## Tasks

### 1. Shared UI components

Migrate `web/src/components/` to `src/components/`. For each component, implement the React
equivalent preserving the same props API where possible.

Priority components:
- `Card` — wrapper with optional `header` slot → `children` + `header` prop
- `Button` — thin wrapper, keep class API
- `Alert` — error display
- `Modal` — `[shadcn]` Option A: use `Dialog` from shadcn. Option B: portal-based overlay with `createPortal` + `focus-trap-react`
- `DataTable` — rebuild with TanStack Table v8; same props: `headers`, `onFetch`
  (async, returns `{ items, currentPage, lastPage }`)
- `Form` + `FormField` + `FormInput` — rebuild with React Hook Form; preserve Yup validation via `@hookform/resolvers/yup`
- `FormSelect` with async search — `[shadcn]` Option A: use `Combobox` from shadcn. Option B: custom controlled input + dropdown with `focus-trap-react` for keyboard handling
- `Popover` — `[shadcn]` Option A: use `Popover` from shadcn. Option B: custom positioned overlay
- `Pagination` — controlled component driven by DataTable
- `CadAttachmentEditor` — file upload + list; see Vue source for props
- `MeshAttachmentEditor` — same pattern as CadAttachmentEditor

### 2. Utility functions

Create `src/utils/formatters.ts` with functions replacing Vue filters:
- `formatDatetime(value: string): string` — replaces `| datetime` filter
- Any other filters found during the Phase 0 audit

### 3. `sign_in` view

File: `src/views/signin.tsx`

Flow:
1. On mount, if `?code=` query param is present: call `sessionService.create(...)`,
   store token, redirect to `/`
2. Otherwise: show "Sign in" button that redirects to the LemonLDAP auth URL
   (read from `VITE_AUTH_URL` env var)
3. Show error alert on failure

### 4. `home` dashboard

File: `src/views/home/index.tsx`

Uses `react-chartjs-2` for pie charts (sites by status, magnets by status). Same data
fetching pattern as Vue version. Register Chart.js components explicitly (required in v3+).

### 5. CRUD views (Materials, Parts, Magnets, Sites)

Each entity has 4 views: list, show, new, edit. Implement as a pattern, then replicate:

**List view** (`/materials`):
- `DataTable` component with server-side pagination + sort
- Link to new, link to show per row

**Show view** (`/materials/:id`):
- Display fields in a `Card`
- Edit and delete actions
- Attachment editors where applicable (CAD, Mesh on Part/Magnet)

**New / Edit views**:
- `Form` with `FormField` components
- Yup validation schema (reuse from Vue source)
- On success: navigate to show view

Note: `Magnet` and `Part` views are the most complex — they include `CadAttachmentEditor`,
`MeshAttachmentEditor`, status management, and JSON config fields rendered in Monaco Editor.

### 6. Monaco Editor integration

Use `@monaco-editor/react` package. It replaces direct Monaco usage. Wrap it in a
`JsonEditor` component that handles loading state and onChange:

```tsx
import Editor from '@monaco-editor/react';

function JsonEditor({ value, onChange }) {
  return (
    <Editor
      height="300px"
      language="json"
      value={value}
      onChange={onChange}
    />
  );
}
```

### 7. Simulation views

File: `src/views/simulations/`

The most complex views. Key challenges:
- Show view includes **real-time log streaming** via WebSocket
- Status polling (simulation can be queued, running, complete, failed)
- Large JSON setup_state rendered/edited in Monaco

Implement a `useSimulationStream` custom hook:
```ts
function useSimulationStream(simulationId: number) {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<string>('');

  useEffect(() => {
    const ws = new WebSocket(`${WS_ENDPOINT}/api/simulations/${simulationId}/stream`);
    ws.onmessage = (event) => { /* parse and update logs/status */ };
    return () => ws.close();
  }, [simulationId]);

  return { logs, status };
}
```

### 8. Admin views

- `admin/config` — key/value config editor
- `admin/users` — DataTable + show/edit user
- `admin/audit-logs` — DataTable with datetime formatting

---

## Per-component deliverables

For each migrated component or view, provide:
1. The `.tsx` source file
2. A Vitest test file covering: renders without crashing, key interactions, error states

---

## Constraints

- No class components — functional components + hooks only
- All API calls go through `src/services/client.ts`
- No direct `localStorage` access — all auth state via `useAuthStore`
- File downloads (attachments) use `window.open(...)` with `auth_token` query param,
  same pattern as Vue app
- WebSocket URL from `VITE_WS_ENDPOINT` env variable
