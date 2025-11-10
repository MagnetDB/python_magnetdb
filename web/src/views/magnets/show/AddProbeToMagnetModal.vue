<template>
  <Modal :visible="visible" @close="$emit('close')" :closeable="true">
    <template #header>
      Add a probe
    </template>
    <template>
      <Form ref="form" @submit="submit" @validate="validate">
        <FormField
            label="Probe Name"
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
            label="Index"
            name="index"
            type="text"
            placeholder="e.g., U1,U2,U3 (comma-separated)"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Locations"
            name="locations"
            type="text"
            placeholder="e.g., [0,0,0],[0,0,1],[0,0,2] (comma-separated JSON arrays)"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Part (Optional)"
            name="part"
            :component="FormSelect"
            :options="partOptions"
            @search="searchPart"
        />
        <FormField
            label="Metadata"
            name="metadata"
            type="text"
            placeholder="{}"
            :component="FormInput"
        />
      </Form>
    </template>
    <template #footer>
      <div class="flex items-center space-x-2">
        <Button type="button" class="btn btn-primary" @click="$refs.form.submit()">
          Save
        </Button>
        <Button class="btn btn-outline-default" @click="$emit('close')">
          Cancel
        </Button>
      </div>
    </template>
  </Modal>
</template>

<script>
import * as Yup from 'yup'
import * as partService from '@/services/partService'
import * as probeService from '@/services/probeService'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormSelect from "@/components/FormSelect";
import FormInput from "@/components/FormInput";
import Button from "@/components/Button";
import Modal from "@/components/Modal";

export default {
  name: 'AddProbeToMagnetModal',
  props: ['visible', 'magnetId'],
  components: {
    Modal,
    Button,
    FormField,
    Form,
  },
  data() {
    return {
      FormSelect,
      FormInput,
      partOptions: [],
      typeOptions: [
        { name: 'Voltage', value: 'voltage' },
        { name: 'Current', value: 'current' },
        { name: 'Temperature', value: 'temperature' },
        { name: 'Pressure', value: 'pressure' },
        { name: 'Field', value: 'field' },
      ],
    }
  },
  methods: {
    searchPart(query, loading) {
      loading(true)
      partService.list()
        .then((parts) => {
          this.partOptions = parts.items.map((item) => ({name: item.name, value: item.id, part: item}))
        })
        .finally(() => loading(false))
    },
    parseIndex(indexStr) {
      // Parse comma-separated index values
      if (!indexStr) return []
      return indexStr.split(',').map(s => s.trim())
    },
    parseLocations(locationsStr) {
      // Parse comma-separated JSON arrays like [0,0,0],[0,0,1],[0,0,2]
      if (!locationsStr) return []
      try {
        const matches = locationsStr.match(/\[[^\]]+\]/g)
        if (!matches) return []
        return matches.map(m => JSON.parse(m))
      } catch (e) {
        throw new Error('Invalid locations format. Use comma-separated JSON arrays: [0,0,0],[0,0,1]')
      }
    },
    submit(values, {setRootError}) {
      try {
        const payload = {
          name: values.name,
          description: values.description || '',
          type: values.type.value,
          index: this.parseIndex(values.index),
          locations: this.parseLocations(values.locations),
          magnet_id: this.magnetId,
        }

        if (values.part) {
          payload.part_id = values.part.value
        }

        if (values.metadata) {
          payload.metadata = values.metadata
        }

        return probeService.create(payload)
          .then(() => this.$emit('close', true))
          .catch(setRootError)
      } catch (error) {
        setRootError(error.message)
      }
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        type: Yup.object().required(),
        index: Yup.string().required(),
        locations: Yup.string().required(),
      })
    },
  },
  async mounted() {
    const parts = await partService.list()
    this.partOptions = parts.items.map((item) => ({name: item.name, value: item.id, part: item}))
  }
}
</script>
