import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { createStore } from 'vuex'

function buildStore() {
  return createStore({
    state: {
      token: localStorage.getItem('magnetdb_session_token'),
      user: null,
    },
    getters: {
      isLogged(state) {
        return !!state.token
      },
    },
    mutations: {
      setToken(state, token) {
        state.token = token
        if (token) {
          localStorage.setItem('magnetdb_session_token', token)
        } else {
          localStorage.removeItem('magnetdb_session_token')
          state.user = null
        }
      },
      setUser(state, user) {
        state.user = user
      },
    },
  })
}

describe('store', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('initialises token from localStorage', () => {
    localStorage.setItem('magnetdb_session_token', 'pre-existing')
    const store = buildStore()
    expect(store.state.token).toBe('pre-existing')
  })

  it('initialises with null token when localStorage is empty', () => {
    const store = buildStore()
    expect(store.state.token).toBeNull()
  })

  it('setToken persists token to localStorage and sets state', () => {
    const store = buildStore()
    store.commit('setToken', 'abc123')
    expect(store.state.token).toBe('abc123')
    expect(localStorage.getItem('magnetdb_session_token')).toBe('abc123')
  })

  it('setToken(null) removes from localStorage and clears token and user', () => {
    const store = buildStore()
    store.commit('setToken', 'abc123')
    store.commit('setUser', { id: 1 })
    store.commit('setToken', null)
    expect(store.state.token).toBeNull()
    expect(store.state.user).toBeNull()
    expect(localStorage.getItem('magnetdb_session_token')).toBeNull()
  })

  it('isLogged returns true when token is set', () => {
    const store = buildStore()
    store.commit('setToken', 'tok')
    expect(store.getters.isLogged).toBe(true)
  })

  it('isLogged returns false when token is null', () => {
    const store = buildStore()
    expect(store.getters.isLogged).toBe(false)
  })
})
