import { describe, it, expect, beforeEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createStore } from 'vuex'
import { defineComponent } from 'vue'

const Stub = defineComponent({ template: '<div />' })

function buildStore(token = null) {
  return createStore({
    state: { token, user: null },
    getters: {
      isLogged: (state) => !!state.token,
    },
    mutations: {
      setToken(state, t) { state.token = t },
    },
  })
}

function buildRouter(store) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { name: 'home', path: '/', component: Stub },
      { name: 'magnets', path: '/magnets', component: Stub },
      { name: 'sites', path: '/sites', component: Stub },
      { name: 'sign_in', path: '/sign_in', component: Stub },
    ],
  })

  router.beforeEach(async (to, _, next) => {
    if (to.name !== 'sign_in' && !store.getters.isLogged) {
      return next({ name: 'sign_in' })
    }
    return next()
  })

  return router
}

describe('router guard', () => {
  let store

  beforeEach(() => {
    store = buildStore()
  })

  it('redirects unauthenticated user from / to sign_in', async () => {
    const router = buildRouter(store)
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('sign_in')
  })

  it('redirects unauthenticated user from /magnets to sign_in', async () => {
    const router = buildRouter(store)
    await router.push('/magnets')
    expect(router.currentRoute.value.name).toBe('sign_in')
  })

  it('allows unauthenticated user to reach /sign_in', async () => {
    const router = buildRouter(store)
    await router.push('/sign_in')
    expect(router.currentRoute.value.name).toBe('sign_in')
  })

  it('allows authenticated user to reach protected route', async () => {
    store = buildStore('valid-token')
    const router = buildRouter(store)
    await router.push('/magnets')
    expect(router.currentRoute.value.name).toBe('magnets')
  })

  it('allows authenticated user to reach /', async () => {
    store = buildStore('valid-token')
    const router = buildRouter(store)
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('home')
  })
})
