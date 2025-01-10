import { get, set, cloneDeep } from 'lodash'
import QueueRunner from "@/utils/QueueRunner";

export const queue = new QueueRunner()

export function createFormField() {
  return {
    inject: ['form'],
    methods: {
      onInput(event) {
        this.setValue(this.fieldName, event.target.value)
      },
      setValue(name, value) {
        queue.run(() => {
          const values = cloneDeep(this.form.values)
          set(values, name, value)
          this.form.setValues(values)
        })
      },
    },
    computed: {
      fieldName() {
        return this.$props.name
      },
      value() {
        return get(this.form.values, this.fieldName)
      },
      errors() {
        return get(this.form.errors, this.fieldName) || []
      }
    }
  }
}
