import client from "./client";

export function list({ query, page, perPage, sortBy, sortDesc, status, type } = {}) {
  return client.get('/api/parts', {
    params: {
      page,
      query,
      status,
      sort_by: sortBy,
      sort_desc: sortDesc,
      per_page: perPage,
      type,
    },
  })
    .then((res) => res.data)
}

export function find({ id }) {
  return client.get(`/api/parts/${id}`)
    .then((res) => res.data)
}

export function create(values) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      form.append(key, value)
    }
  }
  return client.post(`/api/parts`, form)
    .then((res) => res.data)
}

export function update({ id, ...values }) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      form.append(key, value)
    }
  }
  return client.patch(`/api/parts/${id}`, form)
    .then((res) => res.data)
}

export function defunct({ partId }) {
  return client.post(`/api/parts/${partId}/defunct`)
    .then((res) => res.data)
}

export function createGeometry({ partId, ...values }) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      form.append(key, value)
    }
  }
  return client.post(`/api/parts/${partId}/geometries`, form)
    .then((res) => res.data)
}

export function deleteGeometry({ partId, type }) {
  return client.delete(`/api/parts/${partId}/geometries/${type}`).then((res) => res.data)
}
