import client from "./client";

export function list({ query, page, perPage, sortBy, sortDesc, status } = {}) {
  return client.get('/api/sites', {
    params: {
      page,
      query,
      sort_by: sortBy,
      sort_desc: sortDesc,
      per_page: perPage,
      status
    },
  })
    .then((res) => res.data)
}

export function find({ id }) {
  return client.get(`/api/sites/${id}`)
    .then((res) => res.data)
}

export function create(values) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      form.append(key, value)
    }
  }
  return client.post(`/api/sites`, form)
    .then((res) => res.data)
}

export function update({ id, ...values }) {
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value) {
      form.append(key, value)
    }
  }
  return client.patch(`/api/sites/${id}`, form)
    .then((res) => res.data)
}

export function addMagnet({ siteId, magnetId, zOffset, rOffset, parallax }) {
  const form = new FormData()
  form.append('site_id', siteId)
  form.append('magnet_id', magnetId)
  if (zOffset !== undefined) {
    form.append('z_offset', zOffset)
  }
  if (rOffset !== undefined) {
    form.append('r_offset', rOffset)
  }
  if (parallax !== undefined) {
    form.append('parallax', parallax)
  }
  return client.post(`/api/site_magnets`, form).then((res) => res.data)
}

export function deleteMagnet({ siteMagnetId }) {
  return client.delete(`/api/site_magnets/${siteMagnetId}`).then((res) => res.data)
}

export function putInOperation({ siteId }) {
  return client.post(`/api/sites/${siteId}/put_in_operation`)
    .then((res) => res.data)
}

export function shutdown({ siteId }) {
  return client.post(`/api/sites/${siteId}/shutdown`)
    .then((res) => res.data)
}
