<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New simulation
    </div>

    <Card>
      <Form
        :initial-values="{ non_linear: true, static: true }"
        @submit="submit" @validate="validate" @change="computeModelOptions"
      >
        <FormField
            label="Resource"
            name="resource"
            :component="FormSelect"
            :required="true"
            :options="resourceOptions"
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
            label="Geometry"
            name="geometry"
            :component="FormSelect"
            :required="true"
            :options="geometryOptions"
        />
        <FormField
            label="Cooling"
            name="cooling"
            :component="FormSelect"
            :required="true"
            :options="coolingOptions"
        />
        <FormField
            label="Static"
            name="static"
            :component="FormInput"
            type="checkbox"
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
            label="Non-linear"
            name="non_linear"
            :component="FormInput"
            type="checkbox"
            :disabled="true"
        />
        <CurrentsField ref="currents" />
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
import * as siteService from '@/services/siteService'
import * as simulationService from '@/services/simulationService'
import Card from '@/components/Card.vue'
import Form from "@/components/Form.vue";
import FormField from "@/components/FormField.vue";
import FormInput from "@/components/FormInput.vue";
import FormSelect from "@/components/FormSelect.vue";
import Button from "@/components/Button.vue";
import CurrentsField from "../CurrentsField.vue";

export default {
  name: 'SimulationNew',
  components: {
    CurrentsField,
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
      methodOptions: ['cfpdes', 'CG', 'HDG', 'CRB'],
      modelOptions: [],
      geometryOptions: ['Axi', '3D'],
      coolingOptions: ['mean', 'grad', 'meanH', 'gradH', 'gradHZ'],
      resourceOptions: [],
      availableModels: [],
    }
  },
  methods: {
    computeModelOptions(values) {
      this.modelOptions = this.availableModels
          .filter((model) =>
            model.method === values.method && model.geometry === values.geometry &&
            (model.time === (values.static ? 'static' : 'transient'))
          )
          .map((model) => model.model)
    },
    submit(values, {setRootError}) {
      return simulationService.create({
        resource_type: values.resource.value?.type,
        resource_id: values.resource.value?.id,
        method: values.method,
        geometry: values.geometry,
        cooling: values.cooling,
        static: values.static ?? false,
        model: values.model,
        non_linear: values.non_linear ?? false,
        currents: this.$refs.currents.magnets.map(
          (magnet) => ({ magnet_id: magnet.id, value: parseFloat(values[`i_${magnet.id}`]) })
        )
      })
          .then((simulation) => {
            this.$router.push({ name: 'simulation', params: { id: simulation.id } })
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        resource: Yup.mixed().required(),
        method: Yup.string().required(),
        model: Yup.string().oneOf(this.modelOptions).required(),
        geometry: Yup.string().required(),
        cooling: Yup.string().required(),
        ...Object.fromEntries(
          this.$refs.currents.magnets.map(
            (magnet) => [`i_${magnet.id}`, Yup.mixed().required()]
          )
        )
      })
    },
  },
  async mounted() {
    const magnetsRes = await magnetService.list()
    const sitesRes = await siteService.list()
    this.resourceOptions = [
      ...sitesRes.items.map(site => ({
        name: `(Site) ${site.name}`,
        value: { type: 'site', id: site.id },
      })),
      ...magnetsRes.items.map(magnet => ({
        name: `(Magnet) ${magnet.name}`,
        value: { type: 'magnet', id: magnet.id },
      })),
    ]
    this.availableModels = await simulationService.listModels()
  },
}
</script>
