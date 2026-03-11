<template>
  <div class="dashboard">
    <h2>Dashboard</h2>
    <div class="balance-cards">
      <div class="card income">
        <span class="label">Total Income</span>
        <span class="value">{{ formatMoney(balance.total_income) }}</span>
      </div>
      <div class="card expense">
        <span class="label">Total Expenses</span>
        <span class="value">{{ formatMoney(balance.total_expense) }}</span>
      </div>
      <div class="card balance">
        <span class="label">Balance</span>
        <span class="value">{{ formatMoney(balance.balance) }}</span>
      </div>
    </div>
    <div class="chart-section">
      <MonthlyChart :data="monthlySummary" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi } from '../api/reports'
import MonthlyChart from '../components/charts/MonthlyChart.vue'

const balance = ref({ total_income: 0, total_expense: 0, balance: 0 })
const monthlySummary = ref([])

function formatMoney(val) {
  return val.toLocaleString('ru-RU', { minimumFractionDigits: 2 })
}

onMounted(async () => {
  const [bal, summary] = await Promise.all([
    reportsApi.balance(),
    reportsApi.monthlySummary(new Date().getFullYear()),
  ])
  balance.value = bal
  monthlySummary.value = summary
})
</script>
