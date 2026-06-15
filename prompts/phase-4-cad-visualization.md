# Phase 4 — CAD & Scientific Visualization

## Context

MagnetDB React app with all business views migrated (Phase 3 complete). This phase implements
the scientific visualization layer, which did not exist in the Vue 2 app and is being built
fresh in React.

**Decision summary** (from architecture review):
- **vtk.js** (`@kitware/vtk.js`) for 3D CAD geometry and mesh visualization — runs entirely
  in the browser, no separate server process required
- **Plotly.js** (already used) for field maps and 2D scientific plots — consolidate Chart.js
  usage here too
- **trame-react is excluded** — only 6 stars, iframe-based, adds operational complexity
  (separate Python server per session), not production-ready

**Data context** from the MagnetDB data model:
- `CadAttachment` — CAD files linked to `Magnet`, `Part`, or `Site`
- `MeshAttachment` — mesh files with type `axi` (axisymmetric) or `3d`, linked to `Magnet`
  or `Site`
- `Simulation` — has a `mesh_attachment` FK; results are stored as `StorageAttachment`
- Visualisation routes: `/visualisations/bmap`, `/visualisations/bmap_2d`,
  `/visualisations/stress_map`

---

## Goal for this phase

Implement a `<VtkViewer>` component for 3D mesh/geometry rendering and migrate the three
visualisation views to React using Plotly.js. Add download + visualize actions to Magnet,
Part, and Site show views.

---

## Tasks

### 1. Install dependencies

```bash
npm install @kitware/vtk.js plotly.js react-plotly.js
npm install -D @types/plotly.js
```

Note: vtk.js is a large bundle. Configure Vite to handle it:

```ts
// vite.config.ts
export default defineConfig({
  optimizeDeps: {
    exclude: ['@kitware/vtk.js'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vtk: ['@kitware/vtk.js'],
        },
      },
    },
  },
})
```

### 2. `VtkViewer` component

File: `src/components/VtkViewer.tsx`

A self-contained vtk.js viewer that accepts a file URL and renders it in a div.

Requirements:
- Props: `url: string` (URL to fetch the mesh/CAD file from the storage API),
  `type: 'vtp' | 'vtu' | 'stl'`
- Show a loading state while fetching
- Mount vtk.js render window to a `ref` div
- Clean up (call `renderWindow.delete()`) on unmount
- Expose camera reset button
- Handle fetch errors gracefully

Core vtk.js setup pattern:
```ts
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkXMLPolyDataReader from '@kitware/vtk.js/IO/XML/XMLPolyDataReader';

useEffect(() => {
  if (!containerRef.current || !url) return;

  const fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
    rootContainer: containerRef.current,
    background: [0.1, 0.1, 0.1],
  });
  const renderer = fullScreenRenderer.getRenderer();
  const renderWindow = fullScreenRenderer.getRenderWindow();

  // fetch + read + add to scene...

  return () => fullScreenRenderer.delete();
}, [url]);
```

### 3. Axisymmetric mesh viewer

File: `src/components/VtkAxiViewer.tsx`

Variant for `axi` type meshes: applies revolution filter to generate the 3D shape from
the 2D axisymmetric cross-section before rendering.

```ts
import vtkRotationalExtrusionFilter from
  '@kitware/vtk.js/Filters/General/RotationalExtrusionFilter';
```

### 4. Mesh attachment integration

In `MeshAttachmentEditor` (Phase 3), add a "Visualize" action button per attachment that:
- Detects mesh type (`axi` or `3d`)
- Opens a modal containing `<VtkAxiViewer>` or `<VtkViewer>` respectively
- Fetches the file via the storage API with auth token

### 5. Visualisation views (Plotly.js)

Migrate the three routes from the Vue app using Plotly.js / `react-plotly.js`.

#### `/visualisations/bmap` — 3D field map
File: `src/views/visualisations/bmap.tsx`

Renders a 3D Plotly surface or scatter plot of the magnetic field B across a spatial grid.
Fetch data from the API, transform to Plotly `data` format, render with `<Plot>`.

#### `/visualisations/bmap_2d` — 2D field map
File: `src/views/visualisations/bmap-2d.tsx`

2D heatmap / contour plot of B field. Use Plotly `heatmap` or `contour` trace type.
Include axis labels (spatial coordinates) and colorbar (Tesla units).

#### `/visualisations/stress_map` — Stress map
File: `src/views/visualisations/stress-map.tsx`

Similar pattern to bmap_2d but for mechanical stress data from simulations.
Colorbar units: MPa or GPa depending on data.

All three views share a common pattern — extract a `usePlotData(endpoint)` hook:
```ts
function usePlotData(endpoint: string) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    client.get(endpoint)
      .then(res => setData(res.data))
      .catch(setError)
      .finally(() => setLoading(false));
  }, [endpoint]);

  return { data, loading, error };
}
```

### 6. Plotly.js consolidation

Remove `Chart.js` / `react-chartjs-2` from the home dashboard and rewrite the two pie charts
(sites by status, magnets by status) as Plotly `pie` traces. This consolidates all
visualization to a single library.

```tsx
import Plot from 'react-plotly.js';

<Plot
  data={[{ type: 'pie', labels, values }]}
  layout={{ title: 'Sites by status' }}
/>
```

### 7. Performance considerations

- Load `@kitware/vtk.js` lazily (dynamic import) so it doesn't inflate the initial bundle
- Use `React.lazy` + `<Suspense>` for all visualisation views
- Add a `<canvas>` size observer (`ResizeObserver`) to `VtkViewer` so it responds to
  container resizes

---

## Constraints

- vtk.js viewer must clean up all GPU resources on unmount to prevent memory leaks
- File downloads use auth token as query param (same pattern as attachment downloads)
- No trame, no trame-react, no server-side rendering for visualization
- Plotly is the only charting library after this phase (Chart.js removed)
