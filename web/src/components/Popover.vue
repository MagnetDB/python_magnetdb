<template>
  <div class="relative">
    <div @click="active = !active">
      <slot></slot>
    </div>
    <div v-if="active" class="absolute bg-white shadow rounded-md border border-gray-200 w-64 p-4 z-10">
      <slot name="content"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Popover',
  data: () => ({
    active: false,
  }),
}
</script>
