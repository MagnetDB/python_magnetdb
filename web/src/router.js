import VueRouter from "vue-router";
import store from './store'

const router = new VueRouter({
  mode: 'history',
  routes: [
    { name: 'sites', path: '/sites', component: () => import('./views/sites/list') },
    { name: 'new_site', path: '/sites/new', component: () => import('./views/sites/new') },
    { name: 'site', path: '/sites/:id', component: () => import('./views/sites/show') },
    { name: 'new_simulation', path: '/simulations/new', component: () => import('./views/simulations/new/index') },
    { name: 'new_simulation_commissioning', path: '/simulations/new/commissioning', component: () => import('./views/simulations/new/commissioning/index') },
    { name: 'simulation', path: '/simulations/:id', component: () => import('./views/simulations/show') },
    { name: 'simulations', path: '/simulations', component: () => import('./views/simulations/list') },
    { name: 'magnets', path: '/magnets', component: () => import('./views/magnets/list') },
    { name: 'new_magnet', path: '/magnets/new', component: () => import('./views/magnets/new') },
    { name: 'magnet', path: '/magnets/:id', component: () => import('./views/magnets/show') },
    { name: 'materials', path: '/materials', component: () => import('./views/materials/list') },
    { name: 'new_material', path: '/materials/new', component: () => import('./views/materials/new') },
    { name: 'material', path: '/materials/:id', component: () => import('./views/materials/show') },
    { name: 'parts', path: '/parts', component: () => import('./views/parts/list') },
    { name: 'new_part', path: '/parts/new', component: () => import('./views/parts/new') },
    { name: 'part', path: '/parts/:id', component: () => import('./views/parts/show') },
    { name: 'records', path: '/records', component: () => import('./views/records/list') },
    { name: 'new_record', path: '/records/new', component: () => import('./views/records/new') },
    { name: 'record', path: '/records/:id', component: () => import('./views/records/show') },
    { name: 'admin_config', path: '/admin/config', component: () => import('./views/admin/config') },
    { name: 'admin_audit_logs', path: '/admin/audit_logs', component: () => import('./views/admin/audit-logs') },
    { name: 'admin_users', path: '/admin/users', component: () => import('./views/admin/users/list') },
    { name: 'admin_user', path: '/admin/users/:id', component: () => import('./views/admin/users/show') },
    { name: 'profile', path: '/profile', component: () => import('./views/profile') },
    { name: 'servers', path: '/servers', component: () => import('./views/servers/list') },
    { name: 'new_server', path: '/servers/new', component: () => import('./views/servers/new') },
    { name: 'edit_server', path: '/servers/:id/edit', component: () => import('./views/servers/edit') },
    { name: 'visualisation_bmap', path: '/visualisations/bmap', component: () => import('./views/visualisations/bmap') },
    { name: 'visualisation_bmap_2d', path: '/visualisations/bmap_2d', component: () => import('./views/visualisations/bmap-2d') },
    { name: 'visualisation_stress_map', path: '/visualisations/stress_map', component: () => import('./views/visualisations/stress-map') },
    { name: 'home', path: '/', component: () => import('./views/home/index') },
    { name: 'sign_in', path: '/sign_in', component: () => import('./views/signin') }
  ]
})

router.beforeEach(async (to, _, next) => {
  if (to.name !== 'sign_in' && !store.getters.isLogged) {
    return next({ name: 'sign_in' })
  }
  return next()
})

export default router
