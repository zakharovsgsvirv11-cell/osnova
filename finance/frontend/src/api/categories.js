import client from './client'

export const categoriesApi = {
  async list(type = null) {
    const params = type ? { type } : {}
    const { data } = await client.get('/categories', { params })
    return data
  },

  async create(payload) {
    const { data } = await client.post('/categories', payload)
    return data
  },

  async update(id, payload) {
    const { data } = await client.put(`/categories/${id}`, payload)
    return data
  },

  async remove(id) {
    await client.delete(`/categories/${id}`)
  },
}
