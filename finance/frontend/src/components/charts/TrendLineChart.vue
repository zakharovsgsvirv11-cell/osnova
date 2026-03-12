<template>
  <Line :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const props = defineProps({ data: { type: Array, default: () => [] } })

const chartData = computed(() => ({
  labels: props.data.map((d) => d.month),
  datasets: [
    { label: 'Доход', data: props.data.map((d) => d.income), borderColor: '#4CAF50', fill: false },
    { label: 'Расход', data: props.data.map((d) => d.expense), borderColor: '#F44336', fill: false },
  ],
}))

const options = { responsive: true, plugins: { title: { display: true, text: 'Тренд' } } }
</script>
