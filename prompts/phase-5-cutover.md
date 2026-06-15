# Phase 5 — Cutover & Decommission

## Context

MagnetDB React app in `web-react/` is feature-complete (Phases 1–4 done). The Vue 2 app in
`web/` is still running in parallel. This phase switches Traefik to serve the React app,
validates the production deployment, and decommissions the Vue app.

**Infrastructure**: Docker Compose + Traefik for SSL termination and routing.  
**Production**: systemd service management, Debian packaging.  
**Auth**: LemonLDAP::NG SSO — redirect URIs must be updated.

---

## Goal for this phase

Make the React app the production frontend. Remove the Vue app. Clean up Docker, Traefik,
environment config, and CI/CD accordingly.

---

## Pre-cutover checklist

Before switching traffic, verify all of the following in a staging environment:

### Functional parity
- [ ] All routes accessible and rendering correctly
- [ ] Sign-in flow (LemonLDAP redirect → code exchange → token storage) works end-to-end
- [ ] Authenticated API calls work (token in Authorization header)
- [ ] Session persistence across page refresh (Zustand persist middleware)
- [ ] Logout clears token and redirects to `/sign_in`
- [ ] Role-based UI (admin links only for admin users)
- [ ] All CRUD views: list (with pagination + sort), show, new, edit, delete
- [ ] File uploads (CadAttachment, MeshAttachment) work
- [ ] File downloads with auth token work
- [ ] Monaco Editor loads and saves simulation config
- [ ] WebSocket simulation streaming: logs appear in real time
- [ ] vtk.js viewer loads and renders mesh files (axi + 3d)
- [ ] Plotly visualisation views: bmap, bmap_2d, stress_map render with real data
- [ ] Admin views: config, users, audit logs

### Non-functional
- [ ] `npm run build` produces no TypeScript errors
- [ ] All Vitest tests pass
- [ ] Lighthouse performance score acceptable (check bundle size with `vite-bundle-analyzer`)
- [ ] No console errors in production build
- [ ] CORS headers correct for new origin if port/domain changed

---

## Tasks

### 1. Production build configuration

In `web-react/vite.config.ts`, verify:
- `base` URL is correct (if app is served at a subpath)
- Source maps disabled in production
- Chunk splitting configured (vtk.js in its own chunk — see Phase 4)

```ts
build: {
  sourcemap: false,
  rollupOptions: {
    output: {
      manualChunks: {
        vtk: ['@kitware/vtk.js'],
        plotly: ['plotly.js'],
        monaco: ['monaco-editor'],
      },
    },
  },
},
```

### 2. Dockerfile for React app

Create `web-react/Dockerfile` for production:

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

`nginx.conf` must redirect all routes to `index.html` for client-side routing:
```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```

### 3. Traefik configuration update

Update `docker-compose.yml`:
- Point the frontend Traefik router to the `frontend-react` service
- Remove the `frontend` (Vue) service or rename it to `frontend-vue-legacy`
- Ensure SSL termination labels remain on the React service

Example label change:
```yaml
# Before (Vue service)
- "traefik.http.routers.frontend.rule=Host(`magnetdb.lncmi.fr`)"

# After (React service)
- "traefik.http.routers.frontend.rule=Host(`magnetdb.lncmi.fr`)"
```

### 4. LemonLDAP::NG redirect URI

Update the OAuth/OIDC redirect URI in LemonLDAP config if the origin changed. The sign_in
view reads the redirect URI from `window.location.origin`:
```ts
redirect_uri: `${window.location.origin}/sign_in`
```
Verify this matches what is registered in LemonLDAP::NG.

### 5. Environment variables in production

Ensure the following are set in the production environment (not in `.env` files committed
to git):
```
VITE_API_ENDPOINT=https://magnetdb.lncmi.fr
VITE_WS_ENDPOINT=wss://magnetdb.lncmi.fr
VITE_AUTH_URL=https://auth.lncmi.fr/oauth2/authorize?...
```

For Docker, pass via `ARG` / `ENV` in Dockerfile or `environment:` in docker-compose. Note:
Vite bakes env vars into the bundle at build time — they cannot be changed at runtime without
rebuilding.

### 6. Debian packaging update

Update the Debian package build scripts to:
- Build from `web-react/` instead of `web/`
- Copy `web-react/dist/` to the package's static files directory
- Remove Vue build artifacts from the package

### 7. systemd service

Verify the systemd service file (if any) that restarts Docker Compose correctly references
the updated service names.

### 8. Decommission Vue app

Once the React app has been running in production without issues for a defined stabilization
period (suggested: 2 weeks):

1. Archive `web/` directory (git tag: `vue2-final`)
2. Remove `web/` from the repository
3. Remove `frontend` service from `docker-compose.yml`
4. Remove Vue-related dependencies from CI pipeline
5. Update `README.md` to reflect new stack

---

## Rollback plan

If a critical issue is found post-cutover:

1. In Traefik config, re-point the router rule to the `frontend-vue-legacy` service
2. The Vue app image is still available in the Docker registry (do not purge until after
   stabilization period)
3. Estimated rollback time: < 5 minutes (config change + `docker-compose up -d`)

Document the rollback procedure in the project wiki before executing the cutover.

---

## Post-cutover monitoring

For the first 2 weeks after cutover, actively monitor:
- Browser console errors reported by users
- API error rates (401s, 5xxs) in Django logs
- WebSocket connection stability (simulation streaming)
- Memory usage in vtk.js views (check for GPU memory leaks)
- Bundle load time on first visit (Lighthouse / Chrome DevTools)
