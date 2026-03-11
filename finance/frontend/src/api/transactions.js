import client from './client'

export const transactionsApi = {
  async list(params = {}) {
    const { data } = await client.get('/transactions', { params })
    return data
  },

  async create(payload) {
    const { data } = await client.post('/transactions', payload)
    return data
  },

  async update(id, payload) {
    const { data } = await client.put(`/transactions/${id}`, payload)
    return data
  },

  async remove(id) {
    await client.delete(`/transactions/${id}`)
  },
}
