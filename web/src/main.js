import { Chart, registerables } from 'chart.js'
import { install as VueMonacoEditorPlugin } from '@guolao/vue-monaco-editor'
import zoomPlugin from 'chartjs-plugin-zoom'
import Vue from 'vue'
import VueRouter from 'vue-router'
import VueReactiveProvide from 'vue-reactive-provide'
import App from './App.vue'
import router from './router'
import store from './store'
import './main.css'
import * as filters from './filters'

Chart.register(...registerables, zoomPlugin)

Vue.config.productionTip = false
Vue.use(VueReactiveProvide)
Vue.use(VueRouter)
Vue.use(VueMonacoEditorPlugin, {
  paths: {
    // The recommended CDN config
    vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.43.0/min/vs'
  },
})

Vue.prototype.$filters = filters

new Vue({
  render: h => h(App),
  router,
  store,
}).$mount('#app')
