<template>
  <form @submit.prevent="submit">
    <Alert v-if="rootError" class="alert alert-danger mb-4" :error="rootError" />
    <slot />
  </form>
</template>

<script>
import { cloneDeep, isEqual } from 'lodash'
import Alert from "@/components/Alert";

export default {
  name: 'Form',
  props: ['initialValues'],
  components: {
    Alert,
  },
  data() {
    return {
      loading: false,
      values: cloneDeep(this.initialValues || {}),
      errors: {},
      rootError: null,
      dirty: false,
    }
  },
  reactiveProvide: {
    name: 'form',
    include: ['values', 'errors', 'loading', 'dirty', 'submit', 'computeDirty', 'setValues'],
  },
  watch: {
    values: {
      immediate: true,
      deep: true,
      handler() {
        this.computeDirty()
        this.$emit('change', this.values)
      },
    },
    initialValues: {
      immediate: true,
      deep: true,
      handler() {
        this.computeDirty()
      },
    },
  },
  methods: {
    setValues(values) {
      this.values = values
    },
    computeDirty() {
      this.dirty = !isEqual(this.initialValues, this.values)
    },
    async submit() {
      this.errors = await this.validate()
      if (Object.keys(this.errors).length) {
        return
      }

      this.loading = true
      try {
        await this.$listeners.submit(this.values, {
          setErrors: ((errors) => {
            this.errors = errors
          }).bind(this),
          setRootError: ((rootError) => {
            this.rootError = rootError
          }).bind(this),
        })
      } catch {
        // this.errors = errors
      } finally {
        this.loading = false
      }
    },
    async validate() {
      if (!this.$listeners.validate) {
        return {}
      }

      const res = this.$listeners.validate(this.values)
      try {
        await res.validate(this.values, { strict: true, abortEarly: false, recursive: true })
        return {}
      } catch (e) {
        return Object.fromEntries(e.inner.map((error) => [error.path, error.errors]))
      }
    },
  }
}
</script>
