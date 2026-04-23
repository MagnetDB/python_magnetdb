import client from "./client";

export function list({ query, page, perPage, sortBy, sortDesc, status, type } = {}) {
  return client.get('/api/probes', {
    params: {
      page,
      query,
      sort_by: sortBy,
      sort_desc: sortDesc,
      per_page: perPage,
      status,
      'type[]': type
    },
  })
    .then((res) => res.data)
}

export function find({ id }) {
  return client.get(`/api/probes/${id}`)
    .then((res) => res.data)
}

export function create(values) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      if (Array.isArray(value)) {
        value.forEach((item) => form.append(`${key}[]`, item))
      } else {
        form.append(key, value)
      }
    }
  }
  return client.post(`/api/probes`, form)
    .then((res) => res.data)
}

export function update({ id, ...values }) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      if (Array.isArray(value)) {
        value.forEach((item) => form.append(`${key}[]`, item))
      } else {
        form.append(key, value)
      }
    }
  }
  return client.patch(`/api/probes/${id}`, form)
    .then((res) => res.data)
}

export function destroy({ probeId }) {
  return client.delete(`/api/probes/${probeId}`)
    .then((res) => res.data)
}
