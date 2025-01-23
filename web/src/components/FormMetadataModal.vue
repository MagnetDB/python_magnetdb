<template>
  <div class="form-field">
    <label class="form-field-label">Metadata</label>
    <Button :skip-form="true" type="button" class="btn btn-small btn-default" @click="visible = true">
      View metadata
    </Button>
    <Modal :visible="visible" @close="visible = false" :closeable="true">
      <template #header>
        Metadata
      </template>
      <template>
        <div class="h-64">
          <VueMonacoEditor
            theme="vs-light"
            language="json"
            v-model="textValue"
            :options="{
              automaticLayout: true,
              formatOnType: true,
              formatOnPaste: true,
              readOnly: !editable,
            }"
          />
        </div>
      </template>
      <template #footer>
        <div class="flex items-center space-x-2">
          <Button v-if="editable" :skip-form="true" type="button" class="btn btn-primary" @click="submit">
            Save
          </Button>
          <Button :skip-form="true" class="btn btn-outline-default" @click="visible = false">
            Close
          </Button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script>
import Modal from "@/components/Modal.vue";
import VueMonacoEditor from "@guolao/vue-monaco-editor";
import Button from "@/components/Button.vue";
import {createFormField} from "@/mixins/createFormField";

export default {
  props: ['name', 'editable'],
  mixins: [createFormField()],
  data: () => ({
    textValue: '',
    visible: false,
  }),
  watch: {
    value: {
      immediate: true,
      handler(value) {
        this.textValue = JSON.stringify(value, null, 2)
      },
    },
  },
  components: {Button, VueMonacoEditor, Modal},
  methods: {
    submit() {
      this.setValue(this.fieldName, JSON.parse(this.textValue))
      this.visible = false
    },
  },
}
</script>
