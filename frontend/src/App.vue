<script setup>
import { ref, computed } from 'vue'
import AnalysisForm from './components/AnalysisForm.vue'
import PromptManager from './components/PromptManager.vue'
import ResultPanel from './components/ResultPanel.vue'
import RawJson from './components/RawJson.vue'
import ErrorDisplay from './components/ErrorDisplay.vue'
import { getBackendPort } from './api.js'

const result = ref(null)
const error = ref(null)
const loading = ref(false)
const elapsedMs = ref(null)
const currentPort = ref(getBackendPort())
const analysisFormRef = ref(null)

function onPromptsUpdated(prompts) {
  if (analysisFormRef.value) {
    analysisFormRef.value.setAvailablePrompts(prompts)
  }
}

function onPortUpdated() {
  currentPort.value = getBackendPort()
}

let startTime = 0

function onLoading(val) {
  loading.value = val
  if (val) {
    startTime = Date.now()
    elapsedMs.value = null
  } else {
    elapsedMs.value = Date.now() - startTime
  }
}

function onResult(data) {
  result.value = data
  error.value = null
}

function onError(err) {
  error.value = err
  result.value = null
}
</script>

<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="container header-inner">
        <div class="header-brand">
          <span class="header-logo">👁️</span>
          <h1 class="header-title">LazyBrother</h1>
          <span class="header-tag">Debug Client</span>
        </div>
        <span class="header-version">v0.1.0</span>
      </div>
    </header>

    <!-- Main -->
    <main class="main container">
      <div class="layout">
        <!-- Left: Form -->
        <aside class="sidebar">
          <AnalysisForm
            ref="analysisFormRef"
            @result="onResult"
            @error="onError"
            @loading="onLoading"
            @port-updated="onPortUpdated"
          />
          <PromptManager 
            @prompts-updated="onPromptsUpdated"
            @error="onError"
          />
          <div v-if="elapsedMs" class="elapsed">
            Completed in {{ (elapsedMs / 1000).toFixed(1) }}s
          </div>
        </aside>

        <!-- Right: Results -->
        <section class="content">
          <!-- Loading placeholder -->
          <div v-if="loading" class="loading-container">
            <div class="loading-card card">
              <div class="spinner spinner--lg"></div>
              <p class="loading-text">Running analysis pipeline…</p>
              <p class="loading-sub">Fetching data → Patterns → Indicators → SMC → LLM</p>
            </div>
          </div>

          <!-- Error -->
          <ErrorDisplay
            v-else-if="error"
            :error="error"
            @retry="error = null"
          />

          <!-- Results -->
          <template v-else-if="result">
            <ResultPanel :data="result" />
            <RawJson :data="result" />
          </template>

          <!-- Empty state -->
          <div v-else class="empty-state card">
            <div class="empty-icon">📊</div>
            <h3 class="empty-title">Ready to analyze</h3>
            <p class="empty-desc">
              Select a symbol and click <strong>Analyze</strong> to run the pipeline.
            </p>
          </div>
        </section>
      </div>
    </main>

    <!-- Footer -->
    <footer class="footer">
      <div class="container footer-inner">
        <span>LazyBrother Debug Client</span>
        <span>Backend: <code>localhost:{{ currentPort }}</code></span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.header {
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  padding-bottom: 14px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-logo {
  font-size: 1.4rem;
}

.header-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.header-tag {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent);
  background: var(--accent-glow);
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.header-version {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

/* Main layout */
.main {
  flex: 1;
  padding-top: 28px;
  padding-bottom: 28px;
}

.layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 24px;
  align-items: start;
}

.sidebar {
  position: sticky;
  top: 72px;
}

.elapsed {
  margin-top: 10px;
  text-align: center;
  font-size: 0.72rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  padding-top: 60px;
}

.loading-card {
  text-align: center;
  padding: 48px 40px;
}

.spinner--lg {
  width: 32px;
  height: 32px;
  margin: 0 auto 16px;
  border-width: 3px;
  border-color: var(--accent-glow);
  border-top-color: var(--accent);
}

.loading-text {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 6px;
}

.loading-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 64px 40px;
}

.empty-icon {
  font-size: 2.4rem;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* Content */
.content {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
}

/* Footer */
.footer {
  border-top: 1px solid var(--border);
  margin-top: auto;
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  padding-top: 14px;
  padding-bottom: 14px;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.footer code {
  font-family: var(--font-mono);
  color: var(--accent);
}

/* Responsive */
@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .sidebar {
    position: static;
  }
}
</style>
