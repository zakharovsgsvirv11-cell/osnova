<template>
  <form class="transaction-form" @submit.prevent="handleSubmit">
    <select v-model="form.type" required>
      <option value="доход">Доход</option>
      <option value="расход">Расход</option>
    </select>
    <select v-model="form.category_id" required>
      <option v-for="cat in filteredCategories" :key="cat.id" :value="cat.id">
        {{ cat.name }}
      </option>
    </select>
    <input v-model.number="form.amount" type="number" step="0.01" min="0.01" placeholder="Сумма" required />
    <input v-model="form.date" type="date" required />
    <input v-model="form.description" placeholder="Описание" />
    <button type="submit">{{ editing ? 'Обновить' : 'Добавить' }}</button>
    <button v-if="editing" type="button" @click="$emit('cancel')">Отмена</button>
  </form>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  transaction: { type: Object, default: null },
  editing: { type: Boolean, default: false },
})

const emit = defineEmits(['submit', 'cancel'])

const today = new Date().toISOString().slice(0, 10)
const form = reactive({ type: 'расход', category_id: null, amount: null, date: today, description: '' })

const filteredCategories = computed(() =>
  props.categories.filter((c) => c.type === form.type)
)

watch(() => props.transaction, (val) => {
  if (val) {
    form.type = val.type
    form.category_id = val.category_id
    form.amount = val.amount
    form.date = val.date
    form.description = val.description || ''
  }
}, { immediate: true })

function handleSubmit() {
  emit('submit', { ...form })
  if (!props.editing) {
    form.amount = null
    form.description = ''
  }
}
</script>
