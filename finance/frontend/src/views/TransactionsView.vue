<template>
  <div class="transactions-page">
    <h2>Транзакции</h2>

    <div class="categories-section">
      <button class="toggle-categories" @click="showCategories = !showCategories">
        {{ showCategories ? 'Скрыть категории' : 'Управление категориями' }}
      </button>

      <div v-if="showCategories" class="categories-panel">
        <CategoryForm
          :category="editingCat"
          :editing="!!editingCat"
          @submit="handleCategorySubmit"
          @cancel="editingCat = null"
        />
        <ul class="categories-list" v-if="financeStore.categories.length">
          <li v-for="cat in financeStore.categories" :key="cat.id" class="category-item">
            <span class="category-color" :style="{ background: cat.color || '#9E9E9E' }"></span>
            <span class="category-name">{{ cat.name }}</span>
            <span class="category-type">{{ cat.type }}</span>
            <button @click="editingCat = cat">Редактировать</button>
            <button @click="handleCategoryDelete(cat.id)">Удалить</button>
          </li>
        </ul>
        <p v-else class="empty-hint">Категорий пока нет. Создайте первую категорию выше.</p>
      </div>
    </div>

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
import { categoriesApi } from '../api/categories'
import TransactionForm from '../components/TransactionForm.vue'
import TransactionTable from '../components/TransactionTable.vue'
import CategoryForm from '../components/CategoryForm.vue'

const financeStore = useFinanceStore()
const editingTx = ref(null)
const editingCat = ref(null)
const showCategories = ref(false)
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

async function handleCategorySubmit(form) {
  if (editingCat.value) {
    await categoriesApi.update(editingCat.value.id, form)
    editingCat.value = null
  } else {
    await categoriesApi.create(form)
  }
  await financeStore.loadCategories()
}

async function handleCategoryDelete(id) {
  await categoriesApi.remove(id)
  await financeStore.loadCategories()
}

onMounted(loadData)
</script>
