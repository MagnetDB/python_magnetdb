<template>
  <Card>
    <template #header>
      <div class="flex justify-between items-center">
        <div class="flex items-center">
          {{ title || 'Visualize' }}
          <div v-if="dataSampled" class="ml-2 badge badge-primary">
            Data currently sampled
          </div>
        </div>
        <Button class="btn btn-default btn-small" @click="resetZoom">
          Reset zoom
        </Button>
      </div>
    </template>

    <Alert v-if="error" class="alert alert-danger mb-6" :error="error"/>

    <Form :initial-values="{ x: xField, y: yField }" @submit="submit">
      <div class="flex items-center space-x-4">
        <div class="w-1/3">
          <FormField
            label="X Axis"
            name="x"
            :component="FormSelect"
            :options="columnOptions"
            :clearable="false"
          />
        </div>
        <div class="w-1/3">
          <FormField
            label="Y Axis"
            name="y"
            :component="FormSelect"
            :options="columnOptions"
            :clearable="false"
            :multiple="true"
          />
        </div>
      </div>
      <div class="w-2/6">

      </div>
      <div class="flex items-center space-x-4">
        <Button type="submit" class="btn btn-primary btn-small">
          Update
        </Button>


      </div>
    </Form>

    <canvas ref="chart"></canvas>
  </Card>
</template>

<script>
import { markRaw } from 'vue'
import { Chart } from 'chart.js'
import Alert from "@/components/Alert";
import Card from "@/components/Card";
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormSelect from "@/components/FormSelect";
import * as recordService from '@/services/recordService'

function getRandomColor() {
  const letters = '0123456789ABCDEF'
  let color = '#'
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)]
  }
  return color
}

export default {
  name: 'VisualisationCard',
  props: ['recordId', 'title', 'useRouting'],
  components: {
    Form,
    FormField,
    Alert,
    Card,
  },
  data() {
    return {
      FormSelect: markRaw(FormSelect),
      error: null,
      columnOptions: [],
      xField: 't',
      yField: ['Field'],
      xMin: null,
      xMax: null,
      yMin: null,
      yMax: null,
      skipNextZoom: false,
      autoSampling: true,
      dataSampled: false,
      chart: null,
      colors: {},
    }
  },
  methods: {
    submit(values) {
      this.xField = values.x
      this.yField = values.y
      return this.fetch()
    },
    async fetch() {
      let payload = {
        id: this.recordId,
        x: this.xField,
        y: this.yField,
        autoSampling: this.autoSampling,
      }
      if (this.xMin && this.xMax && this.yMin && this.yMax) {
        payload = {
          ...payload,
          xMin: this.xMin,
          xMax: this.xMax,
          yMin: this.yMin,
          yMax: this.yMax,
        }
      }
      return recordService.visualize(payload)
        .then((data) => {
          const entries = Object.entries(data.result).map(([key, values]) => {
            return { key: parseFloat(key), values }
          })
          entries.sort(({ key: a }, { key: b }) => a - b)
          this.chart.data.labels = entries.map((entry) => entry.key)
          this.chart.data.datasets = this.yField.map((fieldName, index) => {
            if (!this.colors[fieldName]) {
              this.colors[fieldName] = getRandomColor()
            }
            return {
              label: `${fieldName} (${data.columns[fieldName]})`,
              backgroundColor: this.colors[fieldName],
              borderColor: this.colors[fieldName],
              data: entries.map(entry => entry.values[index]),
            }
          })
          this.chart.options.scales.x.title.text = `${this.xField} (${data.columns[this.xField]})`
          this.chart.update()
          this.dataSampled = data.sampling_enabled
          this.columnOptions = Object.keys(data.columns)

          if (this.useRouting) {
            this.$router.replace({
              ...this.$route,
              query: {
                chartState: window.btoa(JSON.stringify({
                  x: this.xField,
                  y: this.yField,
                  xMin: this.xMin,
                  xMax: this.xMax,
                  yMin: this.yMin,
                  yMax: this.yMax,
                  colors: this.colors,
                }))
              },
            })
          }
        })
        .catch((error) => {
          this.error = error
        })
    },
    onZoomComplete({ chart }) {
      if (this.skipNextZoom) {
        this.skipNextZoom = false
        return this.fetch()
      }
      this.xMin = chart.scales.x.ticks[0].label
      this.xMax = chart.scales.x.ticks[chart.scales.x.ticks.length - 1].label
      this.yMin = chart.scales.y.min
      this.yMax = chart.scales.y.max
      this.skipNextZoom = true
      this.chart.resetZoom()
    },
    resetZoom() {
      this.xMin = null
      this.xMax = null
      this.yMin = null
      this.yMax = null
      this.skipNextZoom = true
      this.chart.resetZoom()
    },
  },
  created() {
    if (this.$route.query.chartState && this.useRouting) {
      try {
        const data = JSON.parse(window.atob(this.$route.query.chartState))
        this.xField = data.x
        this.yField = data.y
        this.xMin = data.xMin
        this.xMax = data.xMax
        this.yMin = data.yMin
        this.yMax = data.yMax
        this.colors = data.colors
      } catch (error) {
        console.error(error)
      }
    }
  },
  async mounted() {
    this.chart = new Chart(this.$refs.chart, {
      type: 'line',
      data: {
        labels: [],
        datasets: [],
      },
      options: {
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: ''
            }
          },
        },
        plugins: {
          zoom: {
            zoom: {
              drag: {
                enabled: true
              },
              mode: 'xy',
              onZoomComplete: this.onZoomComplete,
            },
          }
        },
      },
    })
    await this.fetch()
  },
  destroyed() {
    this.chart?.destroy()
  }
}
</script>
