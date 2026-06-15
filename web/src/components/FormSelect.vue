<template>
  <VueSelect
    v-bind="$attrs"
    label="name"
    :class="{ 'form-select-error': hasError, 'form-select-disabled': disabled }"
    :modelValue="value"
    @update:modelValue="onInput"
    :options="options"
    :disabled="disabled"
    :clearable="clearable"
    :multiple="multiple"
  />
</template>

<script>
import 'vue-select/dist/vue-select.css'
import VueSelect from 'vue-select'

export default {
  name: 'FormSelect',
  components: {
    VueSelect,
  },
  props: ['hasError', 'options', 'value', 'disabled', 'defaultValue', 'clearable', 'multiple'],
  methods: {
    onInput(event) {
      this.$emit('value', event)
    },
  },
  created() {
    if (this.defaultValue) {
      const option = this.options?.find(opt => opt.value === this.defaultValue)
      if (option) {
        this.$emit('value', option)
      }
    }
  },
}
</script>

<style>
.vs__dropdown-toggle {
  @apply focus:ring-blue-500 focus:border-blue-500 shadow-sm sm:text-sm border-gray-300 rounded-md;
  padding: 0.5rem 0.75rem;
  height: 38px;
}

.vs__search,
.vs__search:focus {
  font-size: 0.875rem;
  line-height: 1.25rem;
  margin: 0;
  padding: 0;
}

.vs__selected {
  margin: 0;
  padding: 0;
  line-height: 1.25rem;
  font-size: 0.875rem;
  @apply space-x-4;
}

.vs__actions {
  padding: 0;
}

.vs--multiple .vs__selected-options {
  @apply space-x-2;
}

.vs--multiple .vs__selected {
  @apply px-2 flex items-center space-x-2 text-xs leading-5 rounded-full whitespace-nowrap;
}

.form-select-error > .vs__dropdown-toggle {
  @apply ring-1 border-red-500 ring-red-500 !important;
}

.form-select-disabled > .vs__dropdown-toggle {
  @apply bg-gray-100 cursor-not-allowed;
}

.vs--disabled .vs__search,
.vs--disabled .vs__clear {
  @apply hidden;
}
</style>
