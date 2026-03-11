import client from './client'

export const reportsApi = {
  async monthlySummary(year) {
    const { data } = await client.get('/reports/monthly-summary', { params: { year } })
    return data
  },

  async categoryBreakdown(params) {
    const { data } = await client.get('/reports/category-breakdown', { params })
    return data
  },

  async trend(months = 12) {
    const { data } = await client.get('/reports/trend', { params: { months } })
    return data
  },

  async balance() {
    const { data } = await client.get('/reports/balance')
    return data
  },
}
