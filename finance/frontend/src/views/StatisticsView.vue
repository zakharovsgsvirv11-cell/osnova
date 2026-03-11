<template>
  <div class="statistics-page">
    <h2>Statistics</h2>
    <ReportSelector @change="selectedReport = $event" />

    <div class="report-content">
      <MonthlyChart v-if="selectedReport === 'monthly-summary'" :data="monthlySummary" />
      <CategoryPieChart v-if="selectedReport === 'category-breakdown'" :data="categoryBreakdown" />
      <TrendLineChart v-if="selectedReport === 'trend'" :data="trendData" />

      <div v-if="selectedReport === 'balance'" class="balance-summary">
        <p>Income: {{ balance.total_income?.toLocaleString('ru-RU') }}</p>
        <p>Expenses: {{ balance.total_expense?.toLocaleString('ru-RU') }}</p>
        <p><strong>Balance: {{ balance.balance?.toLocaleString('ru-RU') }}</strong></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { reportsApi } from '../api/reports'
import ReportSelector from '../components/ReportSelector.vue'
import MonthlyChart from '../components/charts/MonthlyChart.vue'
import CategoryPieChart from '../components/charts/CategoryPieChart.vue'
import TrendLineChart from '../components/charts/TrendLineChart.vue'

const selectedReport = ref('monthly-summary')
const monthlySummary = ref([])
const categoryBreakdown = ref([])
const trendData = ref([])
const balance = ref({})

async function loadReport(report) {
  const year = new Date().getFullYear()
  switch (report) {
    case 'monthly-summary':
      monthlySummary.value = await reportsApi.monthlySummary(year)
      break
    case 'category-breakdown':
      categoryBreakdown.value = await reportsApi.categoryBreakdown({
        date_from: `${year}-01-01`,
        date_to: `${year}-12-31`,
        type: 'expense',
      })
      break
    case 'trend':
      trendData.value = await reportsApi.trend(12)
      break
    case 'balance':
      balance.value = await reportsApi.balance()
      break
  }
}

watch(selectedReport, loadReport)
onMounted(() => loadReport(selectedReport.value))
</script>
