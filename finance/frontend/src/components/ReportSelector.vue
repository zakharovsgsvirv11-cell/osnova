<template>
  <div class="report-selector">
    <select v-model="selectedReport" @change="$emit('change', selectedReport)">
      <option value="monthly-summary">Месячная сводка</option>
      <option value="category-breakdown">По категориям</option>
      <option value="trend">Тренд</option>
      <option value="balance">Баланс</option>
    </select>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineEmits(['change'])
const selectedReport = ref('monthly-summary')
</script>
