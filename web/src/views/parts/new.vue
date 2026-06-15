<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New part
    </div>

    <Card>
      <Form @submit="submit" @validate="validate">
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
            :options="[
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
            ]"
        />
        <FormField
            label="Design Office Reference"
            name="design_office_reference"
            type="text"
            :component="FormInput"
        />
        <FormField
            label="Material"
            name="material"
            :component="FormSelect"
            :required="true"
            :options="materialOptions"
            @search="searchMaterial"
        />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as Yup from 'yup'
import * as partService from '@/services/partService'
import * as materialService from '@/services/materialService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Button from "@/components/Button";
import FormUpload from "@/components/FormUpload";

export default {
  name: 'PartNew',
  components: {
    Button,
    FormField,
    Form,
    Card,
  },
  data() {
    return {
      FormInput: markRaw(FormInput),
      FormSelect: markRaw(FormSelect),
      FormUpload: markRaw(FormUpload),
      error: null,
      materialOptions: [],
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
    submit(values, {setRootError}) {
      return partService.create({
        ...values,
        type: values.type.value,
        material_id: values.material.value,
      })
          .then((part) => {
            this.$router.push({ name: 'part', params: { id: part.id } })
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        type: Yup.mixed().required(),
        material: Yup.mixed().required(),
      })
    },
  },
  async mounted() {
    const res = await materialService.list()
    this.materialOptions = res.items.map(item => ({name: item.name, value: item.id}))
  },
}
</script>
