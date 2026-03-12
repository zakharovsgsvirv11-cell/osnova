<template>
  <form class="category-form" @submit.prevent="handleSubmit">
    <input v-model="form.name" placeholder="Название категории" required />
    <select v-model="form.type" required>
      <option value="доход">Доход</option>
      <option value="расход">Расход</option>
    </select>
    <input v-model="form.color" type="color" />
    <button type="submit">{{ editing ? 'Обновить' : 'Создать' }}</button>
    <button v-if="editing" type="button" @click="$emit('cancel')">Отмена</button>
  </form>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  category: { type: Object, default: null },
  editing: { type: Boolean, default: false },
})

const emit = defineEmits(['submit', 'cancel'])

const form = reactive({ name: '', type: 'расход', color: '#4CAF50' })

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
