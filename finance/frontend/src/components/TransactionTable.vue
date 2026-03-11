<template>
  <div class="transaction-table">
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Type</th>
          <th>Category</th>
          <th>Amount</th>
          <th>Description</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tx in transactions" :key="tx.id" :class="tx.type">
          <td>{{ tx.date }}</td>
          <td>{{ tx.type }}</td>
          <td>{{ getCategoryName(tx.category_id) }}</td>
          <td class="amount">{{ formatAmount(tx.amount, tx.type) }}</td>
          <td>{{ tx.description }}</td>
          <td>
            <button @click="$emit('edit', tx)">Edit</button>
            <button @click="$emit('delete', tx.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  transactions: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
})

defineEmits(['edit', 'delete'])

function getCategoryName(id) {
  const cat = props.categories.find((c) => c.id === id)
  return cat ? cat.name : '—'
}

function formatAmount(amount, type) {
  const sign = type === 'income' ? '+' : '-'
  return `${sign}${amount.toLocaleString('ru-RU', { minimumFractionDigits: 2 })}`
}
</script>
