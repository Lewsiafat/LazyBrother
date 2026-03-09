<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { analyzeSymbol, healthCheck, getBackendPort, setBackendPort } from '../api.js'

const emit = defineEmits(['result', 'error', 'loading', 'port-updated'])

const symbol = ref('BTCUSDT')
const market = ref('crypto')
const mode = ref('scalping')
const loading = ref(false)
const backendOk = ref(null)
const backendPort = ref(getBackendPort())

let healthInterval = null

const quickPicks = [
  { label: 'BTC', symbol: 'BTCUSDT', market: 'crypto' },
  { label: 'ETH', symbol: 'ETHUSDT', market: 'crypto' },
  { label: 'SOL', symbol: 'SOLUSDT', market: 'crypto' },
  { label: 'AAPL', symbol: 'AAPL', market: 'stock' },
  { label: 'TSLA', symbol: 'TSLA', market: 'stock' },
  { label: 'NVDA', symbol: 'NVDA', market: 'stock' },
]

function applyQuickPick(pick) {
  symbol.value = pick.symbol
  market.value = pick.market
}

function onPortChange() {
  const port = backendPort.value.toString().trim()
  if (!port || isNaN(port)) return
  setBackendPort(port)
  emit('port-updated')
  backendOk.value = null
  checkHealth()
}

async function checkHealth() {
  try {
    await healthCheck()
    backendOk.value = true
  } catch {
    backendOk.value = false
  }
}

async function submit() {
  if (loading.value || !symbol.value.trim()) return
  loading.value = true
  emit('loading', true)
  emit('error', null)

  try {
    const result = await analyzeSymbol({
      symbol: symbol.value.trim().toUpperCase(),
      market: market.value,
      mode: mode.value,
    })
    emit('result', result)
  } catch (err) {
    emit('error', { status: err.status || 500, message: err.message })
  } finally {
    loading.value = false
    emit('loading', false)
  }
}

onMounted(() => {
  checkHealth()
  healthInterval = setInterval(checkHealth, 15000)
})

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
})
</script>

<template>
  <div class="form-container card">
    <div class="form-header">
      <h2 class="form-title">Analysis Request</h2>
      <div class="health-indicator" :class="{
        'health--ok': backendOk === true,
        'health--err': backendOk === false,
        'health--pending': backendOk === null,
      }">
        <span class="health-dot"></span>
        <span class="health-label">
          {{ backendOk === true ? 'Backend online' : backendOk === false ? 'Backend offline' : 'Checking…' }}
        </span>
      </div>
    </div>

    <!-- Backend Port -->
    <div class="port-row">
      <label class="field-label" for="backend-port">Backend Port</label>
      <input
        id="backend-port"
        v-model="backendPort"
        class="input input--port"
        type="number"
        min="1"
        max="65535"
        placeholder="8000"
        @change="onPortChange"
        @blur="onPortChange"
      />
    </div>

    <!-- Quick picks -->
    <div class="quick-picks">
      <button
        v-for="pick in quickPicks"
        :key="pick.symbol"
        class="btn btn--ghost btn--sm"
        :class="{ 'btn--active': symbol === pick.symbol }"
        @click="applyQuickPick(pick)"
      >
        {{ pick.label }}
      </button>
    </div>

    <!-- Form fields -->
    <form class="form-fields" @submit.prevent="submit">
      <div class="field">
        <label class="field-label" for="symbol">Symbol</label>
        <input
          id="symbol"
          v-model="symbol"
          class="input"
          type="text"
          placeholder="e.g. BTCUSDT, AAPL"
          required
        />
      </div>

      <div class="field-row">
        <div class="field">
          <label class="field-label" for="market">Market</label>
          <select id="market" v-model="market" class="input select">
            <option value="crypto">Crypto</option>
            <option value="stock">Stock</option>
          </select>
        </div>

        <div class="field">
          <label class="field-label" for="mode">Mode</label>
          <select id="mode" v-model="mode" class="input select">
            <option value="scalping">Scalping (1m/5m/15m)</option>
            <option value="swing">Swing (15m/1h/4h)</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        class="btn btn--primary btn--full"
        :disabled="loading || !symbol.trim()"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>⚡</span>
        {{ loading ? 'Analyzing…' : 'Analyze' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.form-container {
  width: 100%;
}

/* Backend Port row */
.port-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: var(--bg-tertiary, rgba(255,255,255,0.04));
  border: 1px solid var(--border);
  border-radius: 8px;
}

.port-row .field-label {
  margin-bottom: 0;
  white-space: nowrap;
  flex-shrink: 0;
}

.input--port {
  width: 90px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  padding: 6px 10px;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.form-title {
  font-size: 1.1rem;
  font-weight: 700;
}

/* Health indicator */
.health-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 500;
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: background 0.3s;
}

.health--ok .health-dot {
  background: var(--green);
  box-shadow: 0 0 6px var(--green);
}

.health--err .health-dot {
  background: var(--red);
  box-shadow: 0 0 6px var(--red);
}

.health--pending .health-dot {
  background: var(--yellow);
  animation: pulse 1.5s infinite;
}

.health--ok .health-label { color: var(--green); }
.health--err .health-label { color: var(--red); }
.health--pending .health-label { color: var(--yellow); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Quick picks */
.quick-picks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.btn--active {
  background: var(--accent) !important;
  color: #fff !important;
  border-color: var(--accent) !important;
}

/* Form fields */
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.btn--full {
  width: 100%;
  padding: 12px;
  font-size: 0.95rem;
  margin-top: 4px;
}
</style>
