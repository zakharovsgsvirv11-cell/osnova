<template>
  <Pie :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({ data: { type: Array, default: () => [] } })

const chartData = computed(() => ({
  labels: props.data.map((d) => d.category_name),
  datasets: [
    {
      data: props.data.map((d) => d.total),
      backgroundColor: props.data.map((d) => d.color || '#9E9E9E'),
    },
  ],
}))

const options = { responsive: true, plugins: { title: { display: true, text: 'По категориям' } } }
</script>
