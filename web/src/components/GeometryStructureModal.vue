<template>
  <div>
    <Button :skip-form="true" type="button" class="btn btn-small btn-default" @click="visible = true">
      View geometry structure
    </Button>
    <Modal :visible="visible" @close="visible = false" :closeable="true">
      <template #header>
        Geometry structure
      </template>
      <template>
        <input ref="upload" class="hidden" type="file" @input="importFile">
        <div class="h-64">
          <VueMonacoEditor
            theme="vs-light"
            language="json"
            v-model="value"
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
          <Button v-if="editable" :skip-form="true" class="btn btn-outline-default" @click="$refs.upload.click()">
            Import a file
          </Button>
          <Button :skip-form="true" class="btn btn-outline-default" @click="download">
            Download
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

export default {
  props: ['defaultValue', 'editable'],
  data: () => ({
    value: '',
    visible: false,
  }),
  watch: {
    defaultValue: {
      immediate: true,
      handler(value) {
        this.value = value
      },
    },
  },
  components: {Button, VueMonacoEditor, Modal},
  methods: {
    submit() {
      this.$emit('input', this.value)
      this.visible = false
    },
    importFile(event) {
      event.preventDefault()
      if (event.target.files.length === 0) {
        return
      }

      const file = event.target.files[0]
      if (!file.type.includes('json') && !file.type.includes('json')) {
        return
      }

      const reader = new FileReader()
      reader.addEventListener('loadend', (event) => {
        this.value = event.target.result
      })
      reader.readAsText(file, 'utf8')
    },
    download() {
      const blob = new Blob([this.value], {type: 'application/json'})
      const elem = window.document.createElement('a')
      elem.href = window.URL.createObjectURL(blob)
      elem.download = 'structure.json'
      document.body.appendChild(elem)
      elem.click()
      document.body.removeChild(elem)
    },
  },
}
</script>
