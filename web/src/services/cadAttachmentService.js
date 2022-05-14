import client from "./client";

export function create(values) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      form.append(key, value)
    }
  }
  return client.post(`/api/cad_attachments`, form)
    .then((res) => res.data)
}

export function destroy({ id }) {
  return client.delete(`/api/cad_attachments/${id}`)
    .then((res) => res.data)
}
