<template>
  <div v-if="probe">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <div class="display-1">
          Probe: {{ probe.name }}
        </div>
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
          :options="typeOptions"
        />
        <FormField
          label="Description"
          name="description"
          type="text"
          :component="FormInput"
        />
        <FormField
          label="Labels"
          name="labels"
          type="text"
          :component="FormInput"
          help-text="Comma-separated list of probe labels"
        />
        <FormMetadataModal name="metadata" :editable="true" />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>

    <Card class="mb-6">
      <template #header>
        Associated Magnet
      </template>

      <div v-if="probe.magnet">
        <p class="mb-4">
          <strong>Magnet:</strong>
          <router-link :to="{ name: 'magnet', params: { id: probe.magnet.id } }" class="link">
            {{ probe.magnet.name }}
          </router-link>
        </p>
      </div>
      <div v-else>
        <p class="text-gray-500 italic">No associated magnet</p>
      </div>
    </Card>

    <Card class="mb-6">
      <template #header>
        Associated Part
      </template>

      <div v-if="probe.part">
        <p class="mb-4">
          <strong>Part:</strong>
          <router-link :to="{ name: 'part', params: { id: probe.part.id } }" class="link">
            {{ probe.part.name }}
          </router-link>
        </p>
      </div>
      <div v-else>
        <p class="text-gray-500 italic">No associated part</p>
      </div>
    </Card>

    <Card class="mb-6">
      <template #header>
        Coordinates
      </template>

      <div v-if="probe.points && probe.points.length > 0" class="table-responsive">
        <table>
          <thead class="bg-white">
            <tr>
              <th>Index</th>
              <th>X</th>
              <th>Y</th>
              <th>Z</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(point, idx) in probe.points" :key="idx">
              <td>{{ idx }}</td>
              <td>{{ point[0] }}</td>
              <td>{{ point[1] }}</td>
              <td>{{ point[2] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else>
        <p class="text-gray-500 italic">No coordinates defined</p>
      </div>
    </Card>
  </div>
  <Alert v-else-if="error" class="alert alert-danger" :error="error"/>
</template>

<script>
import * as Yup from 'yup'
import * as probeService from '@/services/probeService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Button from "@/components/Button";
import Alert from "@/components/Alert";
import FormMetadataModal from "@/components/FormMetadataModal.vue";

export default {
  name: 'ProbeShow',
  components: {
    FormMetadataModal,
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
      error: null,
      probe: null,
      initialValues: null,
      typeOptions: [
        { name: 'Voltage Taps', value: 'voltage_taps' },
        { name: 'Temperature', value: 'temperature' },
        { name: 'Magnetic Field', value: 'magnetic_field' },
      ],
    }
  },
  methods: {
    submit(values, {setRootError}) {
      let payload = {
        id: this.probe.id,
        name: values.name,
        type: values.type,
        description: values.description,
        labels: values.labels ? values.labels.split(',').map(l => l.trim()) : [],
        metadata: JSON.stringify(values.metadata),
      }

      return probeService.update(payload)
        .then(this.fetch)
        .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        type: Yup.string().required(),
      })
    },
    fetch() {
      return probeService.find({id: this.$route.params.id})
        .then((probe) => {
          this.probe = probe
          this.initialValues = {
            ...probe,
            type: this.typeOptions.find((opt) => opt.value === probe.type),
            labels: probe.labels ? probe.labels.join(', ') : '',
          }
        })
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