<template>
  <div v-if="visible" ref="container" class="modal-container">
    <div ref="root" class="modal">
      <div v-if="$slots.header" class="modal-header">
        <slot name="header" />
        <button v-if="closeable" type="button" @click="close">
          <XMarkIcon class="w-5 h-5 text-gray-500" />
        </button>
      </div>
      <div class="modal-body">
        <slot />
      </div>
      <div v-if="$slots.footer" class="modal-footer">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>

<script>
import { XMarkIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'Modal',
  props: ['visible', 'closeable'],
  components: {
    XMarkIcon,
  },
  methods: {
    close() {
      this.$emit('close')
    },
    handleClick(event) {
      if (!this.closeable) {
        return
      }
      // Written in ES5 for compatibility with browsers that weren't obsolete
      // yet when the question was posted, although they are now
      var path = event.composedPath ? event.composedPath() : event.path;
      if (path) {
         // You got some path information
         console.log('path defined')
      } else {
         // This browser doesn't supply path information
         console.log('path not defined')
      }
      if (path.includes(this.$refs.container) && !path.includes(this.$refs.root)) {
        this.close()
      }
    },
  },
  mounted() {
    window.addEventListener('click', this.handleClick)
  },
  beforeUnmount() {
    window.removeEventListener('click', this.handleClick)
  }
}
</script>

<style>
.modal-container {
  @apply bg-black bg-opacity-30 w-full h-full fixed top-0 left-0 flex items-center justify-center;
  z-index: 1000000;
}

.modal {
  @apply w-full md:w-1/2 lg:w-1/3 bg-white rounded-md shadow-md border border-gray-300;
}

.modal-header {
  @apply flex items-center justify-between px-4 pt-2 font-bold leading-tight text-gray-900 text-xl;
}

.modal-body {
  @apply p-4;
}

.modal-footer {
  @apply bg-gray-100 px-4 py-2;
}
</style>
