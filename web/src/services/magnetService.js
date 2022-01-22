import client from "./client";

export function list() {
  return client.get('/api/magnets')
    .then((res) => res.data)
}

export function find({ id }) {
  return client.get(`/api/magnets/${id}`)
    .then((res) => res.data)
}

export function create(values) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    form.append(key, value)
  }
  return client.post(`/api/magnets`, form)
    .then((res) => res.data)
}

export function update({ id, ...values }) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    form.append(key, value)
  }
  return client.patch(`/api/magnets/${id}`, form)
    .then((res) => res.data)
}

export function decommissionPart({ magnetId, partId }) {
  return client.post(`/api/magnets/${magnetId}/parts/${partId}/decommission`)
    .then((res) => res.data)
}

export function destroy({ id }) {
  return client.delete(`/api/magnets/${id}`)
    .then((res) => res.data)
}
