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


Vue.filter('datetime', (date) => {
  if (!date) {
    return
  }

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
  }).format(date instanceof Date ? date : new Date(date))
})

Vue.filter('statusName', (status) => ({
  in_stock: 'In stock',
  in_study: 'In study',
  in_operation: 'In operation',
  defunct: 'Defunct',
  pending: 'Pending',
  in_progress: 'In progress',
  done: 'Done',
  failed: 'Failed',
  scheduled: 'Scheduled',
}[status]))

Vue.filter('roleName', (role) => ({
  guest: 'Guest',
  user: 'User',
  designer: 'Designer',
  admin: 'Admin',
}[role]))

new Vue({
  render: h => h(App),
  router,
  store,
}).$mount('#app')
