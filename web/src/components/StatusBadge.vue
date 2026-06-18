<template>
  <div class="badge" :class="{
    'badge-primary': ['in_stock', 'in_study'].includes(status),
    'badge-danger': ['defunct', 'failed'].includes(status),
    'badge-success': ['in_operation', 'done'].includes(status),
    'badge-warning': ['in_progress'].includes(status),
    'badge-default': !['in_stock', 'in_study', 'in_operation', 'defunct', 'done', 'in_progress', 'failed'].includes(status),
  }">
    <slot></slot>
    {{ $filters.statusName(status) }}
  </div>
</template>

<script>
export default {
  name: 'StatusBadge',
  props: ['status'],
}
</script>
