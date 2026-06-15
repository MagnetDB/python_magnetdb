import { Chart, registerables } from 'chart.js'
import { install as VueMonacoEditorPlugin } from '@guolao/vue-monaco-editor'
import zoomPlugin from 'chartjs-plugin-zoom'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './main.css'
import * as filters from './filters'

Chart.register(...registerables, zoomPlugin)

const app = createApp(App)

app.use(store)
app.use(router)
app.use(VueMonacoEditorPlugin, {
  paths: {
    vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.43.0/min/vs'
  },
})

app.config.globalProperties.$filters = filters

app.mount('#app')
