<template>
  <Modal :visible="visible" @close="$emit('close')" :closeable="true">
    <template #header>
      Add a part
    </template>
    <template>
      <Form ref="form" @submit="submit" @validate="validate" @change="computeFormChanges">
        <FormField
            label="Part"
            name="part"
            :component="FormSelect"
            :required="true"
            :options="partOptions"
            @search="searchPart"
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
        <FormField
            v-if="displayAngleField"
            label="Angle"
            name="angle"
            type="number"
            placeholder="0"
            :component="FormInput"
            :required="true"
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
import * as magnetService from '@/services/magnetService'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormSelect from "@/components/FormSelect";
import FormInput from "@/components/FormInput";
import Button from "@/components/Button";
import Modal from "@/components/Modal";

export default {
  name: 'AddPartToMagnetModal',
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
      displayAngleField: false,
    }
  },
  methods: {
    computeFormChanges(values) {
      this.displayAngleField = ['ring', 'helix'].includes(values.part?.part?.type)
    },
    searchPart(query, loading) {
      loading(true)
      partService.list({ query, status: ['in_study', 'in_stock'] })
        .then((parts) => {
          this.partOptions = parts.items.map((item) => ({name: item.name, value: item.id, part: item}))
        })
        .finally(() => loading(false))
    },
    submit(values, {setRootError}) {
      let payload = {
        magnetId: this.magnetId,
        partId: values.part.value,
        innerBore: values.inner_bore,
        outerBore: values.outer_bore,
      }
      if (this.displayAngleField) {
        payload.angle = values.angle
      }

      return magnetService.addPart(payload)
        .then(() => this.$emit('close', true))
        .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        part: Yup.object().required(),
        inner_bore: Yup.mixed().required(),
        outer_bore: Yup.mixed().required(),
        ...(this.displayAngleField ? {angle: Yup.mixed().required()} : {})
      })
    },
  },
  async mounted() {
    const parts = await partService.list({ status: ['in_study', 'in_stock'] })
    this.partOptions = parts.items.map((item) => ({name: item.name, value: item.id, part: item}))
  }
}
</script>
