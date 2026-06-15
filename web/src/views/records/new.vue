<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New record
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
            label="Site"
            name="site"
            :component="FormSelect"
            :required="true"
            :options="siteOptions"
        />
        <FormField
            label="File"
            name="attachment"
            type="file"
            :required="true"
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
import * as recordService from '@/services/recordService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Button from "@/components/Button";
import FormUpload from "@/components/FormUpload";

export default {
  name: 'RecordNew',
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
      siteOptions: [],
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return recordService.create({
        name: values.name,
        site_id: values.site.value,
        attachment: values.attachment,
      })
          .then((record) => {
            this.$router.push({ name: 'record', params: { id: record.id } })
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
        site: Yup.mixed().required(),
        attachment: Yup.mixed().required(),
      })
    },
  },
  async mounted() {
    const sitesRes = await siteService.list()
    this.siteOptions = sitesRes.items.map(site => ({
      name: site.name,
      value: site.id,
    }))
  },
}
</script>
