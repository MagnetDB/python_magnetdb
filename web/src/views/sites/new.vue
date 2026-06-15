<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New site
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
            label="Config file"
            name="config"
            type="file"
            :component="FormUpload"
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
import * as siteService from '@/services/siteService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";

export default {
  name: 'SiteNew',
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
      error: null,
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return siteService.create(values)
          .then((site) => {
            this.$router.push({ name: 'site', params: { id: site.id } })
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
      })
    },
  },
}
</script>
