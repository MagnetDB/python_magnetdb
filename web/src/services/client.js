import axios from 'axios'

const client = axios.create({
  baseURL: process.env.API_ENDPOINT || 'http://localhost:8000'
})

export default client
