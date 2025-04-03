<template>
  <div v-if="simulation">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center justify-start space-x-4">
        <div class="display-1">Simulation #{{simulation.id}}</div>
        <StatusBadge :status="simulation.status">Simulation</StatusBadge>
        <StatusBadge :status="simulation.setup_status">Setup</StatusBadge>
      </div>
      <div class="flex items-center justify-end space-x-2">
        <Button class="btn btn-primary" @click="runSetup">
          Run Setup
        </Button>
        <Button
          class="btn btn-primary"
          @click="runSimulationModalOpen = true"
          :disabled="simulation.setup_status !== 'done'"
        >
          Run Simulation
        </Button>
      </div>
    </div>

    <RunSimulationModal
      v-model="runSimulationModalOpen"
      :simulation-id="simulation.id"
      @triggered="simulation.status = $event.status"
    />

    <Alert v-if="error" class="alert alert-danger mb-6" :error="error"/>

    <Card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <div>Details</div>
          <Button class="btn btn-danger btn-small" @click="deleteSimulation">
            Delete
          </Button>
        </div>
      </template>

      <Form :initial-values="simulation" @submit="submit">
        <FormField
            label="Resource"
            name="magnet"
            :component="FormSelect"
            :required="true"
            :options="resourceOptions"
            :defaultValue="simulation.resource_id"
            :disabled="true"
        />
        <FormField
            label="Method"
            name="method"
            :component="FormSelect"
            :required="true"
            :options="methodOptions"
            :disabled="true"
        />
        <FormField
            label="Model"
            name="model"
            :component="FormSelect"
            :required="true"
            :options="modelOptions"
            :disabled="true"
        />
        <FormField
            label="Geometry"
            name="geometry"
            :component="FormSelect"
            :required="true"
            :options="geometryOptions"
            :disabled="true"
        />
        <FormField
            label="Cooling"
            name="cooling"
            :component="FormSelect"
            :required="true"
            :options="coolingOptions"
            :disabled="true"
        />
        <FormField
            label="Setup Output"
            name="setup_output"
            :component="FormUpload"
            :disabled="true"
            :default-value="simulation.setup_output_attachment"
        />
        <div class="flex items-center space-x-4">
          <FormField
              label="Simulation Output"
              name="output"
              :component="FormUpload"
              :disabled="true"
              :default-value="simulation.output_attachment"
              class="w-full"
          />
          <div v-if="simulation.log_attachment" class="whitespace-nowrap">
            <a :href="logAttachmentUrl" class="btn btn-primary" target="_blank" style="margin-top: 12px; height: 38px">
              View logs
            </a>
          </div>
        </div>
        <FormField
            label="Static"
            name="static"
            :component="FormInput"
            type="checkbox"
            :disabled="true"
            :checked="simulation.static"
        />
        <FormField
            label="Non-linear"
            name="non_linear"
            :component="FormInput"
            type="checkbox"
            :disabled="true"
            :checked="simulation.non_linear"
        />
        <FormField
            label="Mesh"
            name="mesh"
            :component="FormSelect"
            :required="true"
            :options="meshOptions"
            :clearable="true"
            :disabled="true"
        />
        <FormField
            v-for="(current, index) in simulation.currents"
            :key="current.magnet.id"
            :label="`Current for ${current.magnet.name}`"
            :name="`currents.${index}.value`"
            :component="FormInputWithUnit"
            type="number"
            :required="true"
            :disabled="true"
            :default-value="current.value"
            :unit-options="[
              {
                name: 'Ampère',
                value: 'A',
                symbol: 'A',
                default: true,
              },
              {
                name: 'Kilo Ampère',
                value: 'kA',
                symbol: 'kA',
                default: false,
              }
            ]"
        />
        <FormMetadataModal name="metadata" :editable="true" />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>

    <MeasuresCard :simulation-id="simulation.id" />
  </div>
  <Alert v-else-if="error" class="alert alert-danger" :error="error"/>
</template>

<script>
import * as simulationService from '@/services/simulationService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormInputWithUnit from "@/components/FormInputWithUnit";
import FormSelect from "@/components/FormSelect";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";
import Alert from "@/components/Alert";
import StatusBadge from "@/components/StatusBadge";
import MeasuresCard from "@/views/simulations/show/MeasuresCard";
import RunSimulationModal from "@/views/simulations/show/RunSimulationModal";
import client from "@/services/client";
import FormMetadataModal from "@/components/FormMetadataModal.vue";

export default {
  name: 'SimulationShow',
  components: {
    FormMetadataModal,
    RunSimulationModal,
    MeasuresCard,
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
      FormInputWithUnit,
      FormSelect,
      FormUpload,
      error: null,
      simulation: null,
      runSimulationModalOpen: false,
      resourceOptions: [],
      methodOptions: ['cfpdes', 'CG', 'HDG', 'CRB'],
      modelOptions: ['thelec', 'mag', 'thmag', 'thmagel', 'mag_hcurl', 'thmag_hcurl', 'thmagel_hcurl'],
      geometryOptions: ['Axi', '3D'],
      coolingOptions: ['mean', 'grad', 'meanH', 'gradH', 'gradHZ'],
      meshOptions: [],
    }
  },
  computed: {
    logAttachmentUrl() {
      return `${client.defaults.baseURL}/api/attachments/${this.simulation.log_attachment_id}/download?auth_token=${this.$store.state.token}`
    },
  },
  methods: {
    submit(values) {
      return simulationService.update({
        id: this.simulation.id,
        metadata: JSON.stringify(values.metadata),
      })
    },
    deleteSimulation() {
      return simulationService.deleteSimulation({ id: this.simulation.id })
          .then(() => this.$router.push({ name: 'simulations' }))
          .catch((err) => alert(err.message))
    },
    runSetup() {
      return simulationService.runSetup({ id: this.simulation.id })
          .then((res) => this.simulation.setup_status = res.setup_status)
          .catch((err) => alert(err.message))
    },
  },
  async mounted() {
    try {
      this.simulation = await simulationService.find({id: this.$route.params.id})
      this.resourceOptions = [
        {
          name: `${this.simulation.resource.name} (${this.simulation.resource_type})`,
          value: this.simulation.resource_id,
        }
      ]
      if (this.simulation.mesh) {
        this.meshOptions = [
          {
            name: `(${this.simulation.mesh.type.toUpperCase()}) ${this.simulation.mesh.attachment.filename}`,
            value: this.simulation.mesh.id,
          }
        ]
        this.simulation.mesh = this.meshOptions[0]
      }
    } catch (error) {
      this.error = error
    }
  },
}
</script>
