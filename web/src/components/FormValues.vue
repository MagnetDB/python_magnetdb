<script>
export default {
  name: 'FormValues',
  inject: ['form'],
  render() {
    return this.$slots.default({ values: this.form.values })
  },
}
</script>
