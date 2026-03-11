<template>
  <div class="report-selector">
    <select v-model="selectedReport" @change="$emit('change', selectedReport)">
      <option value="monthly-summary">Monthly Summary</option>
      <option value="category-breakdown">Category Breakdown</option>
      <option value="trend">Trend</option>
      <option value="balance">Balance</option>
    </select>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineEmits(['change'])
const selectedReport = ref('monthly-summary')
</script>
