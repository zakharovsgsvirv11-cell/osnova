<template>
  <div class="transactions-page">
    <h2>Транзакции</h2>

    <TransactionForm
      :categories="financeStore.categories"
      :transaction="editingTx"
      :editing="!!editingTx"
      @submit="handleSubmit"
      @cancel="editingTx = null"
    />

    <TransactionTable
      :transactions="financeStore.transactions"
      :categories="financeStore.categories"
      @edit="editingTx = $event"
      @delete="handleDelete"
    />

    <div class="pagination" v-if="financeStore.transactionsMeta.total > financeStore.transactionsMeta.per_page">
      <button :disabled="page === 1" @click="page--; loadData()">Назад</button>
      <span>Страница {{ page }}</span>
      <button @click="page++; loadData()">Вперёд</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFinanceStore } from '../stores/finance'
import { transactionsApi } from '../api/transactions'
import TransactionForm from '../components/TransactionForm.vue'
import TransactionTable from '../components/TransactionTable.vue'

const financeStore = useFinanceStore()
const editingTx = ref(null)
const page = ref(1)

async function loadData() {
  await Promise.all([
    financeStore.loadCategories(),
    financeStore.loadTransactions({ page: page.value }),
  ])
}

async function handleSubmit(form) {
  if (editingTx.value) {
    await transactionsApi.update(editingTx.value.id, form)
    editingTx.value = null
  } else {
    await transactionsApi.create(form)
  }
  await financeStore.loadTransactions({ page: page.value })
}

async function handleDelete(id) {
  await transactionsApi.remove(id)
  await financeStore.loadTransactions({ page: page.value })
}

onMounted(loadData)
</script>
