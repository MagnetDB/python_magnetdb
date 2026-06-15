<template>
  <button class="root" :class="{ loading: currentlyLoading, disabled: currentlyDisabled }" @click.prevent="onClick">
    <div v-if="currentlyLoading" class="loader">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="animate-spin">
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
    <slot />
  </button>
</template>

<script>
export default {
  name: 'Button',
  inheritAttrs: false,
  props: ['loading', 'disabled', 'skipForm'],
  data() {
    return { internalLoading: false }
  },
  inject: {
    form: { default: null },
  },
  computed: {
    currentlyLoading() {
      return this.loading || (!this.skipForm && this.form?.loading) || this.internalLoading
    },
    currentlyDisabled() {
      return this.disabled || this.currentlyLoading || (!this.skipForm && this.form && !this.form.dirty)
    },
  },
  methods: {
    async onClick() {
      this.internalLoading = true
      try {
        if (this.$attrs.onClick) {
          await this.$attrs.onClick()
        } else if (this.form) {
          await this.form.submit()
        }
      } finally {
        this.internalLoading = false
      }
    }
  },
}
</script>

<style scoped>
.root {
  @apply relative;
}

.disabled {
  @apply opacity-60 pointer-events-none;
}

.loading {
  @apply pointer-events-none;
}

.loader {
  @apply absolute rounded-md flex items-center justify-center z-10 top-0 left-0 w-full h-full;
}

.loader > svg {
  @apply h-5 w-5 text-white;
}

.btn-primary .loader {
  @apply bg-green-500;
}

.btn-default .loader {
  @apply bg-white;
}

.btn-default .loader > svg {
  @apply text-gray-900;
}

.btn-danger .loader {
  @apply bg-red-600;
}
</style>
