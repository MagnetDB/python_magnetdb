<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New server
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
            label="Host"
            name="host"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="SSH username"
            name="username"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Image directory"
            name="image_directory"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <Button type="submit" class="btn btn-primary">
          Create
        </Button>
      </Form>
    </Card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as Yup from 'yup'
import * as serverService from '@/services/serverService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";

export default {
  name: 'ServerNew',
  components: {
    Button,
    FormField,
    Form,
    Card,
  },
  data() {
    return {
      FormInput: markRaw(FormInput),
      FormUpload: markRaw(FormUpload),
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return serverService.create(values)
          .then(() => this.$router.push({ name: 'servers' }))
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        host: Yup.string().required(),
        username: Yup.string().required(),
        image_directory: Yup.string().required(),
      })
    },
  },
}
</script>
