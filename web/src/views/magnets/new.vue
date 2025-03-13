<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New magnet
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
            label="Design Office Reference"
            name="design_office_reference"
            type="text"
            :component="FormInput"
        />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>
  </div>
</template>

<script>
import * as Yup from 'yup'
import * as magnetService from '@/services/magnetService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Button from "@/components/Button";
import FormUpload from "@/components/FormUpload";

export default {
  name: 'MagnetNew',
  components: {
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
      typeOptions: [
        { name: 'Insert', value: 'insert' },
        { name: 'Bitters', value: 'bitters' },
        { name: 'Supras', value: 'supras' },
      ],
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return magnetService.create({ ...values, type: values.type.value })
          .then((magnet) => {
            this.$router.push({ name: 'magnet', params: { id: magnet.id } })
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        type: Yup.mixed().required(),
      })
    },
  },
}
</script>
