import axios from 'axios'
import store from '../store'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000'
})

client.interceptors.request.use((res) => {
  if (store.getters.isLogged) {
    res.headers.Authorization = store.state.token
  }
  return res
})

export default client
