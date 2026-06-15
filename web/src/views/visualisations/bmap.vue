<template>
  <div class="space-y-4">
    <Alert v-if="error" :error="error" class="alert alert-danger"/>

    <div v-if="resource" class="display-1">
      {{ resource.name }}
    </div>

    <Card v-if="params">
      <Form ref="form" :initial-values="params" @change="handleChanges">
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
        <FormValues v-slot="{ values }">
          <div class="flex items-center space-x-4">
            <div class="w-1/3">
              <FormField
                  label="N"
                  name="n"
                  :component="FormSlider"
                  :min="120"
                  :max="1000"
                  :step="1"
              />
            </div>
            <div v-if="values.command === '1D_r'" class="w-1/3">
              <FormField
                  label="R [m]"
                  name="r"
                  :component="FormSlider"
                  :min="0"
                  :max="10"
              />
            </div>
            <div v-if="values.command === '1D_z'" class="w-1/3">
              <FormField
                  label="Z [m]"
                  name="z"
                  :component="FormSlider"
                  :min="-10"
                  :max="10"
              />
            </div>
          </div>
        </FormValues>
        <div class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
                label="R0 [m]"
                name="r0"
                type="number"
                :component="FormInput"
            />
          </div>
          <div class="w-1/3">
            <FormField
                label="Z0 [m]"
                name="z0"
                type="number"
                :component="FormInput"
            />
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="w-1/3">
            <FormField
                label="Pkey"
                name="pkey"
                :component="FormSelect"
                :options="['A', 'Br', 'Bz', 'B', 'dBr/dr', 'dBr/dz', 'dBz/dr', 'dBz/dz', 'G']"
            />
          </div>
          <div class="w-1/3">
            <FormField
                label="Command"
                name="command"
                :component="FormSelect"
                :options="['1D_z', '1D_r']"
            />
          </div>
        </div>
      </Form>
    </Card>
    <Card>
      <canvas ref="chart"></canvas>
    </Card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as visualisationService from '@/services/visualisationService'
import * as siteService from '@/services/siteService'
import * as magnetService from '@/services/magnetService'
import {Chart} from "chart.js";
import Card from "@/components/Card";
import FormSlider from "@/components/FormSlider";
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Alert from "@/components/Alert";
import FormValues from "@/components/FormValues";

export default {
  name: 'BMapVisualisation',
  components: {
    FormValues,
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
        this.error = null
        const {results: data, params, allowed_currents: allowedCurrents} = await visualisationService.bmap({
          ...values,
          resource_id: this.$route.query.resource_id,
          resource_type: this.$route.query.resource_type,
        })
        this.allowedCurrents = allowedCurrents
        this.params = params
        if (!this.chart) {
          this.chart = new Chart(this.$refs.chart, {
            type: 'line',
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
                  title: {
                    display: true,
                    text: ''
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

        this.chart.options.scales.y.title.text = data.yaxis
        if (this.$refs.form) {
          this.chart.data = {
            labels: data.x,
            datasets: [
              {
                label: this.$refs.form.values.pkey,
                backgroundColor: '#FF0000',
                borderColor: '#FF0000',
                data: data.y,
              },
              {
                label: `${this.$refs.form.values.pkey} max`,
                backgroundColor: '#00FF00',
                borderColor: '#00FF00',
                data: data.ymax,
              },
            ],
          }
        }
        this.chart.update()
        this.$router.replace({
          name: this.$route.name,
          query: {
            ...this.$route.query,
            ...params,
          },
        }).catch(() => {
        })
      } catch (error) {
        this.error = error
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
            this.resource = await siteService.find({id: resourceId})
            break
          case 'magnet':
            this.resource = await magnetService.find({id: resourceId})
            break
        }
      })(),
    ])
  }
}
</script>
