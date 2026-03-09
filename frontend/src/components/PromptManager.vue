<script setup>
import { ref, onMounted } from 'vue'
import { listPrompts, deletePrompt, importPromptMarkdown } from '../api.js'

const emit = defineEmits(['error', 'prompts-updated'])

const prompts = ref([])
const loading = ref(false)
const fileInput = ref(null)

async function fetchPrompts() {
  loading.value = true
  try {
    prompts.value = await listPrompts()
    emit('prompts-updated', prompts.value)
  } catch (err) {
    emit('error', err)
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  if (!confirm('Are you sure you want to delete this prompt?')) return
  try {
    await deletePrompt(id)
    await fetchPrompts()
  } catch (err) {
    emit('error', err)
  }
}

function triggerImport() {
  fileInput.value?.click()
}

async function handleImport(event) {
  const file = event.target.files?.[0]
  if (!file) return

  try {
    await importPromptMarkdown(file)
    await fetchPrompts()
  } catch (err) {
    emit('error', err)
  } finally {
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
}

onMounted(() => {
  fetchPrompts()
})

const isCollapsed = ref(true)
</script>

<template>
  <div class="prompt-manager card">
    <div class="header" @click="isCollapsed = !isCollapsed">
      <div class="title-group">
        <h3 class="title">📚 Prompt Manager</h3>
        <span class="badge">{{ prompts.length }}</span>
      </div>
      <span class="toggle" :class="{ 'toggle--open': !isCollapsed }">▼</span>
    </div>

    <div class="content" v-show="!isCollapsed">
      <div class="actions">
        <button class="btn btn--sm btn--ghost" @click="triggerImport" title="Import Markdown">
          <span>📥 Import .md</span>
        </button>
        <button class="btn btn--sm btn--ghost" @click="fetchPrompts" title="Refresh">
          <span>🔄</span>
        </button>
        <input 
          type="file" 
          ref="fileInput" 
          accept=".md" 
          style="display: none" 
          @change="handleImport"
        />
      </div>

      <div class="prompt-list" v-if="prompts.length > 0">
        <div v-for="p in prompts" :key="p.id" class="prompt-item">
          <div class="prompt-info">
            <span class="prompt-name">{{ p.name }}</span>
            <span class="prompt-cat">{{ p.category }}</span>
          </div>
          <button class="btn-delete" @click="handleDelete(p.id)" title="Delete prompt">×</button>
        </div>
      </div>
      <div v-else class="empty-state">
        No custom prompts. Import a .md file to get started!
      </div>
    </div>
  </div>
</template>

<style scoped>
.prompt-manager {
  margin-top: 16px;
  padding: 0;
  overflow: hidden;
}

.header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: var(--bg-tertiary, rgba(255,255,255,0.02));
  transition: background 0.2s;
}

.header:hover {
  background: var(--bg-tertiary, rgba(255,255,255,0.05));
}

.title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.badge {
  background: var(--accent-glow);
  color: var(--accent);
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 700;
}

.toggle {
  font-size: 0.7rem;
  color: var(--text-muted);
  transition: transform 0.3s;
}

.toggle--open {
  transform: rotate(180deg);
}

.content {
  padding: 0 16px 16px;
  border-top: 1px solid var(--border);
}

.actions {
  display: flex;
  gap: 8px;
  margin: 12px 0;
  justify-content: flex-end;
}

.prompt-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
}

.prompt-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.prompt-name {
  font-size: 0.85rem;
  font-weight: 600;
}

.prompt-cat {
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
}

.btn-delete {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-delete:hover {
  color: var(--red);
  background: rgba(255, 0, 0, 0.1);
}

.empty-state {
  text-align: center;
  padding: 24px 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}
</style>
