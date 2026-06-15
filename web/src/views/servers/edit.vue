<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      Edit server
    </div>

    <Card v-if="loaded">
      <Form ref="form" :initial-values="server" @submit="submit" @validate="validate">
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
        <FormField
            label="Type"
            name="type"
            :component="FormSelect"
            :required="true"
            :options="['compute', 'visu']"
        />
        <FormField
            label="SMP"
            name="smp"
            type="checkbox"
            :component="FormInput"
        />
        <FormField
            label="Cores"
            name="cores"
            type="number"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Multithreading"
            name="multithreading"
            type="checkbox"
            :component="FormInput"
        />
        <FormField
            label="Job Manager"
            name="job_manager"
            :component="FormSelect"
            :required="true"
            :options="['none', 'slurm', 'oar']"
        />
        <FormField
            label="Mesh Gems Directory"
            name="mesh_gems_directory"
            type="text"
            :component="FormInput"
            :required="true"
        />

        <Button type="submit" class="btn btn-primary">
          Update
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
import FormSelect from "@/components/FormSelect";
import FormInput from "@/components/FormInput";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";

export default {
  name: 'ServerEdit',
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
      FormSelect: markRaw(FormSelect),
      loaded: false,
      server: null,
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return serverService.update({ id: this.server.id, ...values })
          .then(() => this.$router.push({ name: 'servers' }))
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        host: Yup.string().required(),
        username: Yup.string().required(),
        image_directory: Yup.string().required(),
        type: Yup.string().required(),
        cores: Yup.mixed().required(),
        job_manager: Yup.string().required(),
        mesh_gems_directory: Yup.string().required(),
      })
    },
  },
  mounted() {
    serverService.find({ id: this.$route.params.id })
        .then((server) => {
          this.server = server
        })
        .catch((error) => {
          this.$refs.form.rootError = error
        })
        .finally(() => {
          this.loaded = true
        })
  },
}
</script>
