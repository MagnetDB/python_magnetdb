<template>
  <div class="space-y-4">
    <Alert v-if="error" :error="error" class="alert alert-danger" />

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
        <div v-if="$route.query.resource_type === 'site'" class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
              label="Magnet Type"
              name="magnet_type"
              :component="FormSelect"
              :options="magnetTypeOptions"
            />
          </div>
        </div>
      </Form>
    </Card>
    <Card>
      <LoadingOverlay :loading="loading">
        <canvas ref="chart"></canvas>
      </LoadingOverlay>
    </Card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as visualisationService from '@/services/visualisationService'
import {Chart} from "chart.js";
import Card from "@/components/Card";
import FormSlider from "@/components/FormSlider";
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Alert from "@/components/Alert";
import * as siteService from "@/services/siteService";
import * as magnetService from "@/services/magnetService";
import LoadingOverlay from "@/components/LoadingOverlay.vue";

export default {
  name: 'StressMapVisualisation',
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
      loading: true,
      params: null,
      chart: null,
      error: null,
      resource: null,
      allowedCurrents: [],
      magnetTypeOptions: [
        {name: 'Helices', value: 'H'},
        {name: 'Bitter', value: 'B'},
        {name: 'Supra', value: 'S'},
      ],
    }
  },
  methods: {
    handleChanges(values) {
      return this.fetch(values)
    },
    async fetch(values) {
      this.loading = true
      try {
        const { results: data, params, allowed_currents: allowedCurrents } = await visualisationService.stressMap({
          ...values,
          magnet_type: values.magnet_type?.value,
          resource_id: this.$route.query.resource_id,
          resource_type: this.$route.query.resource_type,
        })
        this.params = {
          ...params,
          magnet_type: this.magnetTypeOptions.find((opt) => opt.value === params.magnet_type),
        }
        this.allowedCurrents = allowedCurrents
        if (!this.chart) {
          this.chart = new Chart(this.$refs.chart, {
            type: 'bar',
            data: {},
            options: {
              scales: {
                x: {
                  title: {
                    display: true,
                    text: '[m]'
                  },
                },
                y: {
                  type: 'linear',
                  title: {
                    display: true,
                    text: '[MPa]'
                  },
                },
              },
              plugins: {
                zoom: {
                  zoom: {
                    drag: {
                      enabled: true
                    },
                    mode: 'xy',
                  },
                }
              },
            },
          })
        }

        this.chart.data = {
          labels: data.x,
          datasets: [
            {
              label: `I`,
              backgroundColor: '#FF0000',
              borderColor: '#FF0000',
              data: data.y,
            },
            {
              label: `I nominal`,
              backgroundColor: '#00FF00',
              borderColor: '#00FF00',
              data: data.ymax,
            },
          ],
        }
        this.chart.update()
        this.$router.replace({
          name: this.$route.name,
          query: {
            ...this.$route.query,
            ...params,
          },
        }).catch(() => {})
        this.loading = false
        this.error = null
      } catch (error) {
        this.error = error
      }
    },
  },
  async mounted() {
    await Promise.all([
      this.fetch({
        ...this.$route.query,
        magnet_type: this.magnetTypeOptions.find((opt) => opt.value === this.$route.query.magnet_type),
      }),
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
