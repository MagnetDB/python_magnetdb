<template>
  <div>
    <div v-if="label" class="form-field-label">
      {{label}}
    </div>
    <div class="attachment-list">
      <div v-for="mesh in attachments" :key="mesh.id" class="attachment">
        <div>
          <b>({{ mesh.type.toUpperCase() }})</b> {{mesh.attachment.filename}}
        </div>
        <div class="attachment-action-list">
          <button @click="removeAttachment(mesh)" class="attachment-action">
            <TrashIcon class="h5 w-5" />
          </button>
          <button class="attachment-action" @click="downloadAttachment(mesh)">
            <DownloadIcon class="h5 w-5" />
          </button>
        </div>
      </div>
      <Button @click="newMeshModalOpen = true" :skip-form="true" class="btn btn-default btn-small">
        Add new mesh
      </Button>
    </div>

    <Modal :visible="newMeshModalOpen" @close="newMeshModalOpen = false" :closeable="true">
      <template #header>
        Add a part
      </template>
      <template>
        <Form ref="form" @submit="submit" @validate="validate">
          <FormField
              label="Type"
              name="type"
              :component="FormSelect"
              :required="true"
              :options="[
                {
                  name: '3D',
                  value: '3d'
                },
                {
                  name: 'Axi',
                  value: 'axi'
                },
              ]"
          />
          <FormField
            label="File"
            name="file"
            type="file"
            :required="true"
            :component="FormUpload"
          />
        </Form>
      </template>
      <template #footer>
        <div class="flex items-center space-x-2">
          <Button :skip-form="true" type="button" class="btn btn-primary" @click="$refs.form.submit()">
            Add mesh
          </Button>
          <Button class="btn btn-outline-default" @click="newMeshModalOpen = false">
            Cancel
          </Button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script>
import client from '@/services/client'
import * as meshAttachmentService from '@/services/meshAttachmentService'
import { TrashIcon } from '@vue-hero-icons/outline'
import { DownloadIcon } from '@vue-hero-icons/outline'
import Button from "@/components/Button";
import Modal from "@/components/Modal.vue";
import FormField from "@/components/FormField.vue";
import FormSelect from "@/components/FormSelect.vue";
import FormUpload from "@/components/FormUpload.vue";
import Form from "@/components/Form.vue";
import * as Yup from "yup";

export default {
  name: 'MeshAttachmentEditor',
  props: ['label', 'resourceType', 'resourceId', 'defaultAttachments'],
  components: {
    Form,
    FormField,
    Modal,
    Button,
    TrashIcon,
    DownloadIcon,
  },
  data() {
    return {
      FormSelect,
      FormUpload,
      attachments: this.defaultAttachments ?? [],
      newMeshModalOpen: false,
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return meshAttachmentService.create({
        file: values.file,
        type: values.type?.value,
        resource_type: this.resourceType,
        resource_id: this.resourceId,
      })
          .then((res) => {
            this.newMeshModalOpen = false
            this.attachments.push(res)
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        type: Yup.mixed().required(),
        file: Yup.mixed().required(),
      })
    },
    removeAttachment(meshAttachment) {
      this.isLoading = true
      meshAttachmentService.destroy({ id: meshAttachment.id })
          .then(() => this.attachments = this.attachments.filter((curr) => curr.id !== meshAttachment.id))
          .catch((err) => {
            alert(err.message)
            console.error(err)
          })
          .finally(() => this.isLoading = false)
    },
    downloadAttachment({ attachment }) {
      window.open(`${client.defaults.baseURL}/api/attachments/${attachment.id}/download?auth_token=${this.$store.state.token}`, '_blank')
    },
  },
}
</script>

<style scoped>
.form-field-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.attachment-list {
  @apply space-y-2 mb-3;
}

.attachment {
  @apply border px-4 pr-2 block w-full shadow-sm sm:text-sm border-gray-300 border-dashed rounded-md cursor-pointer
  flex items-center justify-between h-10;
}

.attachment-action-list {
  @apply flex items-center justify-end space-x-1;
}

.attachment-action {
  @apply hover:bg-gray-200 rounded-md px-1.5 py-1;
}
</style>
