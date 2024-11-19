<template>
  <div>
    <div v-if="label" class="form-field-label">
      {{label}}
    </div>
    <div class="attachment-list">
      <input :key="inputKey" type="file" ref="input" @input="onInput" class="hidden" />
      <div v-for="cadAttachment in attachments" :key="cadAttachment.id" class="attachment">
        {{cadAttachment.attachment.filename}}
        <div class="attachment-action-list">
          <button @click="removeAttachment(cadAttachment)" class="attachment-action">
            <TrashIcon class="h5 w-5" />
          </button>
          <button class="attachment-action" @click="downloadAttachment(cadAttachment)">
            <DownloadIcon class="h5 w-5" />
          </button>
        </div>
      </div>
      <Button @click="openUpload" :skip-form="true" :loading="isLoading" class="btn btn-default btn-small">
        Upload new CAD
      </Button>
    </div>
  </div>
</template>

<script>
import client from '@/services/client'
import * as cadAttachmentService from '@/services/cadAttachmentService'
import { TrashIcon } from '@vue-hero-icons/outline'
import { DownloadIcon } from '@vue-hero-icons/outline'
import Button from "@/components/Button";

export default {
  name: 'CadAttachmentEditor',
  props: ['label', 'resourceType', 'resourceId', 'defaultAttachments'],
  components: {
    Button,
    TrashIcon,
    DownloadIcon,
  },
  data() {
    return {
      attachments: this.defaultAttachments ?? [],
      fileName: false,
      inputKey: Date.now(),
      isLoading: false,
    }
  },
  methods: {
    openUpload() {
      this.inputKey = Date.now()
      this.$refs.input.click()
    },
    onInput(event) {
      const file = event.target.files?.[0]
      if (!file) {
        return
      }

      this.isLoading = true
      cadAttachmentService.create({ resource_type: this.resourceType, resource_id: this.resourceId, file })
          .then((res) => this.attachments.push(res))
          .catch((err) => {
            alert(err.message)
            console.error(err)
          })
          .finally(() => this.isLoading = false)
    },
    removeAttachment(cadAttachment) {
      this.isLoading = true
      cadAttachmentService.destroy({ id: cadAttachment.id })
          .then(() => this.attachments = this.attachments.filter((curr) => curr.id !== cadAttachment.id))
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
