<template>
  <div class="dashboard">
    <h2>Панель управления</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="balance-cards">
      <div class="card income">
        <span class="label">Общий доход</span>
        <span class="value">{{ formatMoney(balance.total_income) }}</span>
      </div>
      <div class="card expense">
        <span class="label">Общие расходы</span>
        <span class="value">{{ formatMoney(balance.total_expense) }}</span>
      </div>
      <div class="card balance">
        <span class="label">Баланс</span>
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
const error = ref('')

function formatMoney(val) {
  return val.toLocaleString('ru-RU', { minimumFractionDigits: 2 })
}

onMounted(async () => {
  try {
    const [bal, summary] = await Promise.all([
      reportsApi.balance(),
      reportsApi.monthlySummary(new Date().getFullYear()),
    ])
    balance.value = bal
    monthlySummary.value = summary
  } catch (e) {
    error.value = 'Не удалось загрузить данные'
    console.error(e)
  }
})
</script>
