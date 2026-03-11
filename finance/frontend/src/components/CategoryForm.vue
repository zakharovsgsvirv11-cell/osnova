<template>
  <form class="category-form" @submit.prevent="handleSubmit">
    <input v-model="form.name" placeholder="Category name" required />
    <select v-model="form.type" required>
      <option value="income">Income</option>
      <option value="expense">Expense</option>
    </select>
    <input v-model="form.color" type="color" />
    <button type="submit">{{ editing ? 'Update' : 'Create' }}</button>
    <button v-if="editing" type="button" @click="$emit('cancel')">Cancel</button>
  </form>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  category: { type: Object, default: null },
  editing: { type: Boolean, default: false },
})

const emit = defineEmits(['submit', 'cancel'])

const form = reactive({ name: '', type: 'expense', color: '#4CAF50' })

watch(() => props.category, (val) => {
  if (val) {
    form.name = val.name
    form.type = val.type
    form.color = val.color || '#4CAF50'
  }
}, { immediate: true })

function handleSubmit() {
  emit('submit', { ...form })
  if (!props.editing) {
    form.name = ''
  }
}
</script>
