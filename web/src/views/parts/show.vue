<template>
  <div v-if="part">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <div class="display-1">
          Part Definition: {{ part.name }}
        </div>
        <StatusBadge :status="part.status"></StatusBadge>
      </div>
      <Button v-if="part.status === 'in_stock'" class="btn btn-danger" type="button" @click="defunct">
        Defunct
      </Button>
    </div>

    <Alert v-if="error" class="alert alert-danger mb-6" :error="error"/>

    <Card class="mb-6">
      <template #header>
        Details
      </template>

      <Form ref="form" :initial-values="part" @submit="submit" @validate="validate">
        <FormField
            label="Name"
            name="name"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Description"
            name="description"
            type="text"
            :component="FormInput"
        />
        <FormField
            label="Type"
            name="type"
            :component="FormSelect"
            :required="true"
            :options="typeOptions"
            :default-value="part.type.toLowerCase()"
        />
        <FormField
            label="Design Office Reference"
            name="design_office_reference"
            type="text"
            :component="FormInput"
        />
        <div class="flex items-center space-x-4">
          <FormField
              label="Material"
              name="material"
              :component="FormSelect"
              :required="true"
              :options="materialOptions"
              :default-value="part.material.id"
              class="w-full"
              @search="searchMaterial"
          />
          <FormValues v-slot="{ values }">
            <router-link
              :to="{ name: 'material', params: { id: values.material.value } }"
              class="btn btn-primary" target="_blank" style="margin-top: 12px; height: 38px"
            >
              Open
            </router-link>
          </FormValues>
        </div>
        <CadAttachmentEditor
            label="CAD"
            resource-type="part"
            :resource-id="part.id"
            :default-attachments="part.cad"
        />
        <div class="form-field">
          <label class="form-field-label">Geometry</label>
          <GeometryModal :default-value="defaultGeometryValue" :editable="true" @input="editGeometry" />
        </div>
        <div v-if="part.allow_hts_file" class="form-field">
          <label class="form-field-label">Geometry HTS</label>
          <GeometryStructureModal
            :default-value="defaultGeometryStructureValue"
            :editable="true"
            @input="editGeometryStructure"
          />
        </div>
        <div v-if="part.allow_shape_file" class="form-field">
          <label class="form-field-label">Geometry shape</label>
          <GeometryShapeModal
            :default-value="defaultGeometryShapeValue"
            :editable="true"
            @input="editGeometryShape"
          />
        </div>
        <FormMetadataModal name="metadata" :editable="true" />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>

    <Card>
      <template #header>
        Magnets
      </template>

      <div class="table-responsive">
        <table>
          <thead class="bg-white">
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="magnetPart in part.magnet_parts" :key="magnetPart.id">
              <td>
                <router-link :to="{ name: 'magnet', params: { id: magnetPart.magnet.id } }" class="link">
                  {{ magnetPart.magnet.name }}
                </router-link>
              </td>
              <td>
                <template v-if="magnetPart.magnet.description">{{ magnetPart.magnet.description }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
              <td>
                <StatusBadge :status="magnetPart.magnet.status"></StatusBadge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
  <Alert v-else-if="error" class="alert alert-danger" :error="error"/>
</template>

<script>
import * as Yup from 'yup'
import * as partService from '@/services/partService'
import * as materialService from '@/services/materialService'
import Card from '@/components/Card.vue'
import Form from "@/components/Form.vue";
import FormField from "@/components/FormField.vue";
import FormInput from "@/components/FormInput.vue";
import FormSelect from "@/components/FormSelect.vue";
import FormUpload from "@/components/FormUpload.vue";
import Button from "@/components/Button.vue";
import Alert from "@/components/Alert.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import CadAttachmentEditor from "@/components/CadAttachmentEditor.vue";
import FormValues from "@/components/FormValues.vue";
import GeometryModal from "@/components/GeometryModal.vue";
import client from "@/services/client";
import {cloneDeep, set} from "lodash";
import {queue} from "@/mixins/createFormField";
import GeometryStructureModal from "@/components/GeometryStructureModal.vue";
import GeometryShapeModal from "@/components/GeometryShapeModal.vue";
import FormMetadataModal from "@/components/FormMetadataModal.vue";

export default {
  name: 'PartShow',
  components: {
    FormMetadataModal,
    GeometryShapeModal,
    GeometryStructureModal,
    GeometryModal,
    FormValues,
    CadAttachmentEditor,
    StatusBadge,
    Alert,
    Button,
    FormField,
    Form,
    Card,
  },
  data() {
    return {
      FormInput,
      FormSelect,
      FormUpload,
      error: null,
      part: null,
      materialOptions: [],
      defaultGeometryValue: '',
      defaultGeometryStructureValue: '',
      defaultGeometryShapeValue: '',
      typeOptions: [
        {
          name: 'Helix',
          value: 'helix'
        },
        {
          name: 'Ring',
          value: 'ring'
        },
        {
          name: 'Lead',
          value: 'lead'
        },
        {
          name: 'Bitter',
          value: 'bitter'
        },
        {
          name: 'Supra',
          value: 'supra'
        },
        {
          name: 'Screen',
          value: 'screen'
        },
      ],
    }
  },
  methods: {
    searchMaterial(query, loading) {
      loading(true)
      materialService.list({ query })
        .then((res) => {
          this.materialOptions = res.items.map(item => ({name: item.name, value: item.id}))
        })
        .finally(() => loading(false))
    },
    defunct() {
      return partService.defunct({ partId: this.part.id })
          .then(this.fetch)
          .catch((error) => {
            this.error = error
          })
    },
    async submit(values, {setRootError}) {
      try {
        let payload = {
          id: this.part.id,
          name: values.name,
          description: values.description,
          type: values.type.value,
          design_office_reference: values.design_office_reference,
          material_id: values.material.value,
          geometry_yaml_config: values.geometry_yaml_config,
          metadata: JSON.stringify(values.metadata),
        }
        if (values.cao instanceof File) {
          payload.cao = values.cao
        }
        if (values.geometry_hts instanceof File) {
          payload.geometry_hts = values.geometry_hts
        }
        if (values.geometry_shape instanceof File) {
          payload.geometry_shape = values.geometry_shape
        }

        await partService.update(payload)
        await this.fetch()
      } catch (error) {
        setRootError(error)
      }
    },
    editGeometry(value) {
      queue.run(() => {
        const values = cloneDeep(this.$refs.form.values)
        set(values, 'geometry_yaml_config', value)
        this.$refs.form.setValues(values)
      })
    },
    editGeometryStructure(value) {
      queue.run(() => {
        const values = cloneDeep(this.$refs.form.values)
        set(values, 'geometry_hts', new File([value], 'structure.json', { type: 'application/json' }))
        this.$refs.form.setValues(values)
      })
    },
    editGeometryShape(value) {
      queue.run(() => {
        const values = cloneDeep(this.$refs.form.values)
        set(values, 'geometry_shape', new File([value], 'shape.csv', { type: 'text/csv' }))
        this.$refs.form.setValues(values)
      })
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        type: Yup.mixed().required(),
        material: Yup.mixed().required(),
      })
    },
    fetch() {
      client.get(`/api/parts/${this.$route.params.id}/geometry.yaml`)
          .then((res) => this.defaultGeometryValue = res.data)

      return partService.find({id: this.$route.params.id})
          .then((part) => {
            this.part = part
            if (part.hts?.id) {
              client.get(`/api/attachments/${part.hts.id}/download`, { responseType: 'text' }).then((res) => {
                this.defaultGeometryStructureValue = res.data instanceof String
                    ? res.data
                    : JSON.stringify(res.data, null, 2)
              })
            }
            if (part.shape?.id) {
              client.get(`/api/attachments/${part.shape.id}/download`, { responseType: 'text' }).then((res) => {
                this.defaultGeometryShapeValue = res.data
              })
            }
          })
          .catch((error) => {
            this.error = error
          })
    },
  },
  async mounted() {
    const materialsRes = await materialService.list()
    this.materialOptions = materialsRes.items.map(material => ({
      name: material.name,
      value: material.id,
    }))
    await this.fetch()
  },
}
</script>
