<template>
  <Bar :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({ data: { type: Array, default: () => [] } })

const chartData = computed(() => ({
  labels: props.data.map((d) => d.month),
  datasets: [
    { label: 'Income', data: props.data.map((d) => d.income), backgroundColor: '#4CAF50' },
    { label: 'Expense', data: props.data.map((d) => d.expense), backgroundColor: '#F44336' },
  ],
}))

const options = { responsive: true, plugins: { title: { display: true, text: 'Monthly Summary' } } }
</script>
