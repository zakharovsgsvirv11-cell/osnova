import client from './client'

export const projectApi = {
  async getData() {
    const { data } = await client.get('/project/data')
    return data
  },

  async getSummary() {
    const { data } = await client.get('/project/summary')
    return data
  },
}
