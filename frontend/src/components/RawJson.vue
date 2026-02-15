<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data: { type: Object, required: true },
})

const expanded = ref(false)
const copied = ref(false)

const jsonStr = computed(() => JSON.stringify(props.data, null, 2))

async function copyJson() {
  try {
    await navigator.clipboard.writeText(jsonStr.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback: select a textarea
    const ta = document.createElement('textarea')
    ta.value = jsonStr.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}
</script>

<template>
  <div class="raw-json card">
    <div class="raw-header">
      <button class="btn btn--ghost btn--sm" @click="expanded = !expanded">
        <span class="toggle-icon" :class="{ 'toggle-open': expanded }">▶</span>
        Raw JSON Response
      </button>
      <button v-if="expanded" class="btn btn--ghost btn--sm" @click="copyJson">
        {{ copied ? '✓ Copied!' : '📋 Copy' }}
      </button>
    </div>
    <Transition name="slide">
      <pre v-if="expanded" class="json-block"><code>{{ jsonStr }}</code></pre>
    </Transition>
  </div>
</template>

<style scoped>
.raw-json {
  overflow: hidden;
}

.raw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toggle-icon {
  display: inline-block;
  transition: transform 0.2s var(--ease);
  font-size: 0.65rem;
}

.toggle-open {
  transform: rotate(90deg);
}

.json-block {
  margin-top: 12px;
  padding: 16px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre;
  tab-size: 2;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s var(--ease);
  max-height: 500px;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
}
</style>
