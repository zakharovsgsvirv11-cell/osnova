import { defineStore } from 'pinia'
import { ref } from 'vue'
import { categoriesApi } from '../api/categories'
import { transactionsApi } from '../api/transactions'

export const useFinanceStore = defineStore('finance', () => {
  const categories = ref([])
  const transactions = ref([])
  const transactionsMeta = ref({ total: 0, page: 1, per_page: 20 })

  async function loadCategories(type = null) {
    categories.value = await categoriesApi.list(type)
  }

  async function loadTransactions(params = {}) {
    const data = await transactionsApi.list(params)
    transactions.value = data.items
    transactionsMeta.value = { total: data.total, page: data.page, per_page: data.per_page }
  }

  return { categories, transactions, transactionsMeta, loadCategories, loadTransactions }
})
