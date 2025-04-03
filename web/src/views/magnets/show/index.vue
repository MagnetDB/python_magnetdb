<template>
  <div v-if="magnet">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <div class="display-1">
          Magnet Definition: {{ magnet.name }}
        </div>
        <StatusBadge :status="magnet.status"></StatusBadge>
      </div>
      <div class="flex items-center space-x-4">
        <Button v-if="magnet.status === 'in_stock'" class="btn btn-danger" type="button" @click="defunct">
          Defunct
        </Button>
        <Popover>
          <Button class="btn btn-default">
            Visualize
          </Button>

          <template #content>
            <div class="space-y-2">
              <router-link
                  class="btn btn-default btn-block"
                  :to="{ name: 'visualisation_bmap', query: { resource_type: 'magnet', resource_id: magnet.id } }"
              >
                BMAP
              </router-link>
              <router-link
                  class="btn btn-default btn-block"
                  :to="{ name: 'visualisation_stress_map', query: { resource_type: 'magnet', resource_id: magnet.id } }"
              >
                Stress map
              </router-link>
              <router-link
                  class="btn btn-default btn-block"
                  :to="{ name: 'visualisation_bmap_2d', query: { resource_type: 'magnet', resource_id: magnet.id } }"
              >
                BMAP 2D
              </router-link>
            </div>
          </template>
        </Popover>
      </div>

    </div>

    <Alert v-if="error" class="alert alert-danger mb-6" :error="error"/>

    <Card class="mb-6">
      <template #header>
        Details
      </template>

      <Form ref="form" :initial-values="initialValues" @submit="submit" @validate="validate">
        <FormField
            label="Name"
            name="name"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <FormField
          label="Type"
          name="type"
          :component="FormSelect"
          :required="true"
          :disabled="true"
          :options="typeOptions"
        />
        <FormField
            label="Description"
            name="description"
            type="text"
            :component="FormInput"
        />
        <FormField
            label="Design Office Reference"
            name="design_office_reference"
            type="text"
            :component="FormInput"
        />
        <FormField
            label="Inner bore"
            name="inner_bore"
            type="number"
            placeholder="0"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Outer bore"
            name="outer_bore"
            type="number"
            placeholder="0"
            :component="FormInput"
            :required="true"
        />
        <div class="form-field">
          <label class="form-field-label">Geometry</label>
          <GeometryModal :default-value="defaultGeometryValue" />
        </div>
        <CadAttachmentEditor
          label="CAD"
          resource-type="magnet"
          :resource-id="magnet.id"
          :default-attachments="magnet.cad"
        />
        <MeshAttachmentEditor
            label="Meshes"
            resource-type="magnet"
            :resource-id="magnet.id"
            :default-attachments="magnet.meshes"
        />
        <div class="form-field">
          <label class="form-field-label">Flow params</label>
          <MagnetFlowParamsModal
            :default-value="defaultFlowParamsValue"
            @input="editFlowParams"
            :editable="true"
          />
        </div>
        <FormMetadataModal name="metadata" :editable="true" />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>

    <Card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <div>Parts</div>
          <Button
              v-if="magnet.status === 'in_study'"
              class="btn btn-primary btn-small"
              @click="addPartModalVisible = true"
          >
            Add a part
          </Button>
        </div>
      </template>

      <div class="table-responsive">
        <table>
          <thead class="bg-white">
            <tr>
              <th class="whitespace-nowrap">Name</th>
              <th class="whitespace-nowrap">Description</th>
              <th class="whitespace-nowrap">Status</th>
              <th class="whitespace-nowrap">Angle</th>
              <th class="whitespace-nowrap">Commissioned At</th>
              <th class="whitespace-nowrap">Decommissioned At</th>
              <th class="whitespace-nowrap"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="magnetPart in magnet.magnet_parts" :key="magnetPart.id">
              <td class="whitespace-nowrap">
                <router-link :to="{ name: 'part', params: { id: magnetPart.part.id } }" class="link">
                  {{ magnetPart.part.name }}
                </router-link>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="magnetPart.part.description">{{ magnetPart.part.description }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
              <td class="whitespace-nowrap">
                <StatusBadge :status="magnetPart.part.status"></StatusBadge>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="magnetPart.angle !== null">{{ magnetPart.angle }}</template>
                <span v-else class="text-gray-500 italic">Not set</span>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="magnetPart.commissioned_at !== null">{{ magnetPart.commissioned_at | datetime }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="magnetPart.decommissioned_at !== null">{{ magnetPart.decommissioned_at | datetime }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
              <td class="whitespace-nowrap">
                <Button
                  v-if="['in_study', 'in_stock'].includes(magnet.status)"
                  class="btn btn-danger btn-small"
                  @click="removePart(magnetPart)"
                >
                  Remove part
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <Card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <div>Related Site</div>
        </div>

      </template>

      <div class="table-responsive">
        <table>
          <thead class="bg-white">
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Status</th>
              <th>Commissioned At</th>
              <th>Decommissioned At</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="siteMagnet in magnet.site_magnets" :key="siteMagnet.id">
              <td>
                <router-link :to="{ name: 'site', params: { id: siteMagnet.site.id } }" class="link">
                  {{ siteMagnet.site.name }}
                </router-link>
              </td>
              <td>
                <template v-if="siteMagnet.site.description">{{ siteMagnet.site.description }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
              <td>
                <StatusBadge :status="siteMagnet.site.status" />
              </td>
              <td>{{ siteMagnet.commissioned_at }}</td>
              <td>{{ siteMagnet.decommissioned_at }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <AddPartToMagnetModal
        :magnet-id="magnet.id"
        :visible="addPartModalVisible"
        :allowed-types="magnet.supported_part_types"
        @close="addPartModalVisible = false; fetch()"
    />
  </div>
  <Alert v-else-if="error" class="alert alert-danger" :error="error"/>
</template>

<script>
import * as Yup from 'yup'
import * as magnetService from '@/services/magnetService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";
import Alert from "@/components/Alert";
import AddPartToMagnetModal from "@/views/magnets/show/AddPartToMagnetModal";
import StatusBadge from "@/components/StatusBadge";
import CadAttachmentEditor from "@/components/CadAttachmentEditor";
import Popover from "@/components/Popover";
import GeometryModal from "@/components/GeometryModal.vue";
import client from "@/services/client";
import FormMetadataModal from "@/components/FormMetadataModal.vue";
import MagnetFlowParamsModal from "@/components/MagnetFlowParamsModal.vue";
import {queue} from "@/mixins/createFormField";
import {cloneDeep, set} from "lodash";
import MeshAttachmentEditor from "@/components/MeshAttachmentEditor.vue";

export default {
  name: 'MagnetShow',
  components: {
    MeshAttachmentEditor,
    MagnetFlowParamsModal,
    FormMetadataModal,
    GeometryModal,
    Popover,
    CadAttachmentEditor,
    StatusBadge,
    AddPartToMagnetModal,
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
      magnet: null,
      addPartModalVisible: false,
      initialValues: null,
      defaultGeometryValue: '',
      defaultFlowParamsValue: '',
      typeOptions: [
        { name: 'Insert', value: 'insert' },
        { name: 'Bitters', value: 'bitters' },
        { name: 'Supras', value: 'supras' },
      ],
    }
  },
  methods: {
    editFlowParams(value) {
      queue.run(() => {
        const values = cloneDeep(this.$refs.form.values)
        set(values, 'flow_params', JSON.parse(value))
        this.$refs.form.setValues(values)
      })
    },
    defunct() {
      return magnetService.defunct({ magnetId: this.magnet.id })
          .then(this.fetch)
          .catch((error) => {
            this.error = error
          })
    },
    submit(values, {setRootError}) {
      let payload = {
        id: this.magnet.id,
        name: values.name,
        description: values.description,
        design_office_reference: values.design_office_reference,
        inner_bore: values.inner_bore,
        outer_bore: values.outer_bore,
        metadata: JSON.stringify(values.metadata),
        flow_params: JSON.stringify(values.flow_params),
      }
      if (values.cao instanceof File) {
        payload.cao = values.cao
      }
      if (values.geometry instanceof File) {
        payload.geometry = values.geometry
      }

      return magnetService.update(payload)
          .then(this.fetch)
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
      })
    },
    fetch() {
      client.get(`/api/magnets/${this.$route.params.id}/geometry.yaml`)
          .then((res) => this.defaultGeometryValue = res.data)
      return magnetService.find({id: this.$route.params.id})
          .then((magnet) => {
            this.magnet = magnet
            this.defaultFlowParamsValue = magnet.flow_params ? JSON.stringify(magnet.flow_params, null, 2) : ''
            this.initialValues = {
              ...magnet,
              type: this.typeOptions.find((opt) => opt.value === this.magnet.type),
              flow_params: this.defaultFlowParamsValue,
            }
          })
          .catch((error) => {
            this.error = error
          })
    },
    removePart(magnetPart) {
      magnetService.deletePart({ magnetPartId: magnetPart.id })
          .then(this.fetch)
          .catch((error) => {
            this.error = error
          })
    },
  },
  async mounted() {
    await this.fetch()
  },
}
</script>
