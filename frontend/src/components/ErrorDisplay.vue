<script setup>
defineProps({
  error: { type: Object, required: true },
})

const emit = defineEmits(['retry'])
</script>

<template>
  <div class="error-display card error-card">
    <div class="error-icon">✕</div>
    <div class="error-body">
      <div class="error-status">Error {{ error.status }}</div>
      <p class="error-message">{{ error.message }}</p>
      <button class="btn btn--ghost btn--sm" @click="emit('retry')">
        ↻ Retry
      </button>
    </div>
  </div>
</template>

<style scoped>
.error-card {
  border-color: rgba(239, 68, 68, 0.3);
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.error-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--red-bg);
  color: var(--red);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 700;
  flex-shrink: 0;
}

.error-status {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--red);
  margin-bottom: 4px;
}

.error-message {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
</style>
