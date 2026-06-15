import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { inject, defineComponent, h } from 'vue'
import Form from '@/components/Form.vue'

// Minimal consumer that renders the injected form fields for inspection
function makeConsumer(captureRef) {
  return defineComponent({
    setup() {
      captureRef.value = inject('form')
      return () => h('div')
    },
  })
}

async function mountForm(options = {}) {
  const { initialValues = {}, onSubmit = async () => {}, onValidate } = options
  const captured = { value: null }
  const Consumer = makeConsumer(captured)

  const wrapper = mount(Form, {
    props: { initialValues },
    attrs: { onSubmit, onValidate },
    slots: { default: () => h(Consumer) },
    global: {
      stubs: { Alert: true },
    },
  })

  return { wrapper, form: captured }
}

describe('Form.vue', () => {
  it('provides a reactive form object to consumers', async () => {
    const { form } = await mountForm({ initialValues: { name: 'test' } })
    expect(form.value).not.toBeNull()
    expect(form.value.values).toEqual({ name: 'test' })
  })

  it('setValues merges new values and consumer sees the update', async () => {
    const { form } = await mountForm({ initialValues: { name: 'old' } })
    form.value.setValues({ name: 'new', extra: 1 })
    // reactive update is synchronous on the reactive object
    expect(form.value.values).toEqual({ name: 'new', extra: 1 })
  })

  it('errors set on form.errors are visible to consumers', async () => {
    const { form } = await mountForm()
    form.value.errors = { name: ['required'] }
    expect(form.value.errors).toEqual({ name: ['required'] })
  })

  it('submit clears errors when validation passes', async () => {
    const { form } = await mountForm({
      initialValues: { name: 'hello' },
      onSubmit: async () => {},
    })
    form.value.errors = { name: ['some error'] }
    await form.value.submit()
    expect(form.value.errors).toEqual({})
  })

  it('submit populates errors when validation fails', async () => {
    const { form } = await mountForm({
      initialValues: { name: '' },
      onValidate: (_values) => ({
        validate: () =>
          Promise.reject({
            inner: [{ path: 'name', errors: ['required'] }],
          }),
      }),
    })
    await form.value.submit()
    expect(form.value.errors).toEqual({ name: ['required'] })
  })

  it('dirty is false when values equal initialValues', async () => {
    const { form } = await mountForm({ initialValues: { name: 'x' } })
    expect(form.value.dirty).toBe(false)
  })

  it('dirty becomes true when values diverge from initialValues', async () => {
    const { form } = await mountForm({ initialValues: { name: 'x' } })
    form.value.values.name = 'y'
    form.value.computeDirty()
    expect(form.value.dirty).toBe(true)
  })

  it('loading is false before submit and false again after', async () => {
    let resolveSubmit
    const { form } = await mountForm({
      onSubmit: () => new Promise((res) => { resolveSubmit = res }),
    })
    expect(form.value.loading).toBe(false)
    const submitPromise = form.value.submit()
    // loading is set after `await validate()`, so flush the microtask queue first
    await Promise.resolve()
    await Promise.resolve()
    expect(form.value.loading).toBe(true)
    resolveSubmit()
    await submitPromise
    expect(form.value.loading).toBe(false)
  })
})
