<template>
  <div class="space-y-4">
    <Alert :error="error" />

    <div v-if="resource" class="display-1">
      {{resource.name}}
    </div>

    <Card v-if="params">
      <Form :initial-values="params" @change="handleChanges">
        <div class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
                v-if="allowedCurrents.includes('i_h')"
                label="I h [A]"
                name="i_h"
                :component="FormSlider"
                :min="0"
                :max="35000"
            />
          </div>
          <div class="w-1/3">
            <FormField
                v-if="allowedCurrents.includes('i_b')"
                label="I b [A]"
                name="i_b"
                :component="FormSlider"
                :min="0"
                :max="35000"
            />
          </div>
          <div class="w-1/3">
            <FormField
                v-if="allowedCurrents.includes('i_s')"
                label="I s [A]"
                name="i_s"
                :component="FormSlider"
                :min="0"
                :max="37000"
            />
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
                label="NR"
                name="nr"
                :component="FormSlider"
                :min="50"
                :max="1000"
                :step="1"
            />
          </div>
          <div class="w-1/3">
            <FormField
                label="R [m]"
                name="r"
                :component="FormSlider"
                :min="0"
                :max="1"
                :step=".01"
            />
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
                label="NZ"
                name="nz"
                :component="FormSlider"
                :min="50"
                :max="1000"
                :step="1"
            />
          </div>
          <div class="w-1/3">
            <FormField
                label="Z [m]"
                name="z"
                :component="FormSlider"
                :min="-1"
                :max="1"
                :step=".01"
            />
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
                label="Pkey"
                name="pkey"
                :component="FormSelect"
                :options="['A', 'Br', 'Bz', 'B']"
            />
          </div>
        </div>
      </Form>
    </Card>
    <Card>
      <LoadingOverlay :loading="loading">
        <div ref="chart"></div>
      </LoadingOverlay>
    </Card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as visualisationService from '@/services/visualisationService'
import * as siteService from '@/services/siteService'
import * as magnetService from '@/services/magnetService'
import Plotly from "plotly.js";
import Card from "@/components/Card";
import FormSlider from "@/components/FormSlider";
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Alert from "@/components/Alert";
import LoadingOverlay from "@/components/LoadingOverlay.vue";

export default {
  name: 'BMap2DVisualisation',
  components: {
    LoadingOverlay,
    Alert,
    FormField,
    Form,
    Card
  },
  data() {
    return {
      FormSlider: markRaw(FormSlider),
      FormInput: markRaw(FormInput),
      FormSelect: markRaw(FormSelect),
      loading: false,
      params: null,
      chart: null,
      error: null,
      resource: null,
      allowedCurrents: [],
    }
  },
  methods: {
    handleChanges(values) {
      return this.fetch(values)
    },
    async fetch(values) {
      try {
        this.loading = true
        const { results: data, params, allowed_currents: allowedCurrents } = await visualisationService.bmap2d({
          ...values,
          z0: values.z?.[0],
          z1: values.z?.[1],
          r0: values.r?.[0],
          r1: values.r?.[1],
          resource_id: this.$route.query.resource_id,
          resource_type: this.$route.query.resource_type,
        })
        this.allowedCurrents = allowedCurrents
        this.params = params

        Plotly.newPlot(this.$refs.chart, [
          {
            z: data.values,
            x: data.x,
            y: data.y,
            type: 'contour'
          }
        ], {}, { responsive: true })

        this.$router.replace({
          name: this.$route.name,
          query: {
            ...this.$route.query,
            ...params,
          },
        }).catch(() => {})
      } catch (error) {
        console.error(error)
        this.error = error
      } finally {
        this.loading = false
      }
    },
  },
  async mounted() {
    await Promise.all([
      this.fetch(this.$route.query),
      (async () => {
        const resourceId = this.$route.query.resource_id
        switch (this.$route.query.resource_type) {
          case 'site':
            this.resource = await siteService.find({ id: resourceId })
            break
          case 'magnet':
            this.resource = await magnetService.find({ id: resourceId })
            break
        }
      })(),
    ])
  }
}
</script>
