<template>
  <Card v-if="measure">
    <template #header>
      <div class="flex justify-between items-center">
        <div class="flex items-center">
          Measures
        </div>
        <FormSelect :value="measure" :options="availableMeasures" @value="fetch" />
      </div>
    </template>

    <div class="table-responsive">
      <table v-if="rows.length > 0">
        <!-- eslint-disable vue/require-v-for-key, vue/valid-v-for -->
        <thead>
          <tr>
            <th v-for="column in columns">
              {{ column }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows">
            <td v-for="value in row">
              {{ value }}
            </td>
          </tr>
        </tbody>
        <!-- eslint-enable vue/require-v-for-key, vue/valid-v-for -->
      </table>
    </div>
  </Card>
</template>

<script>
import { markRaw } from 'vue'
import Card from "@/components/Card";
import * as simulationService from '@/services/simulationService'
import FormSelect from "@/components/FormSelect";

export default {
  name: 'MeasuresCard',
  props: ['simulationId'],
  components: {
    FormSelect: markRaw(FormSelect),
    Card,
  },
  data() {
    return {
      measure: '',
      availableMeasures: [],
      columns: [],
      rows: [],
    }
  },
  methods: {
    async fetch(measure) {
      console.log('MeasureCard fetch (' + this.simulationId + ',' +  measure +')')
      simulationService.getMeasures({ id: this.simulationId, measure: measure })
          .then((data) => {
            this.measure = data.measure
            this.availableMeasures = data.available_measures
            this.columns = data.columns
            this.rows = data.rows
          })
          .catch(console.error)
      console.log(`MeasureCard fetch this.measure=` + this.measure)
    }
      
  },
  async mounted() {
    console.log('MeasureCard mounted')
    this.fetch(null)
  },
}
</script>
