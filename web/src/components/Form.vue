<template>
  <form @submit.prevent="submit">
    <Alert v-if="rootError" class="alert alert-danger mb-4" :error="rootError" />
    <slot />
  </form>
</template>

<script>
import { ref, reactive, provide, watch } from 'vue'
import { cloneDeep, isEqual } from 'lodash'
import Alert from "@/components/Alert"

export default {
  name: 'Form',
  props: ['initialValues'],
  emits: ['change'],
  components: {
    Alert,
  },
  setup(props, { attrs, emit }) {
    const rootError = ref(null)

    function setValues(newValues) {
      form.values = newValues
    }

    function computeDirty() {
      form.dirty = !isEqual(props.initialValues ?? {}, form.values)
    }

    async function validate() {
      if (!attrs.onValidate) return {}
      const schema = attrs.onValidate(form.values)
      try {
        await schema.validate(form.values, { strict: true, abortEarly: false, recursive: true })
        return {}
      } catch (e) {
        return Object.fromEntries(e.inner.map((error) => [error.path, error.errors]))
      }
    }

    async function submit() {
      form.errors = await validate()
      if (Object.keys(form.errors).length) return

      form.loading = true
      try {
        await attrs.onSubmit(form.values, {
          setErrors: (errs) => { form.errors = errs },
          setRootError: (err) => { rootError.value = err },
        })
      } catch {
        // silent
      } finally {
        form.loading = false
      }
    }

    const form = reactive({
      values: cloneDeep(props.initialValues || {}),
      errors: {},
      loading: false,
      dirty: false,
      submit,
      computeDirty,
      setValues,
    })

    provide('form', form)

    watch(() => form.values, () => {
      computeDirty()
      emit('change', form.values)
    }, { immediate: true, deep: true })

    watch(() => props.initialValues, () => {
      computeDirty()
    }, { immediate: true, deep: true })

    return { rootError, submit }
  },
}
</script>
