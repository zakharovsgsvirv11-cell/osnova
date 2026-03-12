<template>
  <div class="project-page">
    <h2>Проект</h2>

    <div v-if="!data.headers.length" class="empty-state">
      <p>Google Sheets не настроен или данные отсутствуют.</p>
      <p>Настройте GOOGLE_SHEET_ID и GOOGLE_SERVICE_ACCOUNT_KEY в .env</p>
    </div>

    <div v-else>
      <div class="project-summary">
        <p>Всего строк: {{ summary.total_rows }}</p>
      </div>

      <table class="project-table">
        <thead>
          <tr>
            <th v-for="header in data.headers" :key="header">{{ header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in data.rows" :key="idx">
            <td v-for="(cell, cidx) in row" :key="cidx">{{ cell }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectApi } from '../api/project'

const data = ref({ headers: [], rows: [] })
const summary = ref({ total_rows: 0 })

onMounted(async () => {
  const [d, s] = await Promise.all([projectApi.getData(), projectApi.getSummary()])
  data.value = d
  summary.value = s
})
</script>
