<template>
  <div class="form-field" :class="fieldClass">
    <div :class="{ 'form-field-inline': inline }">
      <label v-if="label" :for="fieldName" class="form-field-label">
        {{label}}
        <span v-if="required" class="form-field-required">
          &nbsp;*
        </span>
      </label>
      <component
        v-bind="$attrs"
        v-on="$listeners"
        :is="component"
        :id="fieldName"
        :name="fieldName"
        :has-error="errors.length > 0"
        :value="value"
        :inline="inline"
        @input="onInput"
        @value="setValue(fieldName, $event)"
      >
        <slot />
      </component>
    </div>
    <span v-if="errors.length > 0" role="alert" class="form-field-error-message">
      {{ errors[0] }}
    </span>
  </div>
</template>

<script>
import { createFormField } from '@/mixins/createFormField'

export default {
  name: 'FormField',
  inheritAttrs: false,
  props: ['component', 'name', 'inline', 'label', 'required', 'fieldClass'],
  mixins: [createFormField()],
}
</script>

<style>
.form-field {
  @apply mb-3;
}

.form-field-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-field-required {
  @apply text-red-500;
}

.form-field-error-message {
  @apply text-red-500 mt-1 w-full text-sm;
}

.form-field-inline {
  @apply flex items-center;
}

.form-field-inline label {
  @apply m-0 w-1/4;
}
</style>
