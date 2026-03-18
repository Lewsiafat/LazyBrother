<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { saveSnapshot } from '../api.js'

const props = defineProps({
  data: { type: Object, required: true },
})

// ── Snapshot save ────────────────────────────────────────────────────────────
const saveState = ref('idle') // 'idle' | 'saving' | 'saved' | 'error'
const saveError = ref(null)

async function onSave() {
  if (saveState.value === 'saving') return
  saveState.value = 'saving'
  saveError.value = null
  try {
    await saveSnapshot(props.data)
    saveState.value = 'saved'
    setTimeout(() => { saveState.value = 'idle' }, 3000)
  } catch (e) {
    saveError.value = e.message
    saveState.value = 'error'
    setTimeout(() => { saveState.value = 'idle' }, 4000)
  }
}

const analysis = computed(() => props.data.analysis)
const details = computed(() => props.data.details)

const realTimePrice = ref(null)
let ws = null

function connectWebSocket(symbol) {
  if (ws) {
    ws.close()
  }
  
  if (!symbol) return
  
  // Binance WS expects lowercase symbol (e.g. btcusdt@ticker)
  const s = symbol.toLowerCase()
  ws = new WebSocket(`wss://stream.binance.com:9443/ws/${s}@ticker`)
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    realTimePrice.value = parseFloat(data.c) // 'c' is the last price in @ticker stream
  }
  
  ws.onerror = (err) => {
    console.error('WebSocket error:', err)
  }
}

// Watch for symbol changes to reconnect
watch(() => props.data.symbol, (newSymbol) => {
  realTimePrice.value = null
  connectWebSocket(newSymbol)
}, { immediate: true })

onUnmounted(() => {
  if (ws) ws.close()
})

function fmt(n) {
  if (n == null) return '—'
  return typeof n === 'number' ? n.toLocaleString(undefined, { maximumFractionDigits: 6 }) : String(n)
}
</script>

<template>
  <div class="result">
    <!-- Header meta -->
    <div class="result-meta card">
      <div class="meta-left">
        <div class="meta-row">
          <span class="meta-symbol">{{ data.symbol }}</span>
          <span class="badge badge--tag">{{ data.market }}</span>
          <span class="badge badge--tag">{{ data.mode }}</span>
        </div>
        <div class="meta-time">{{ new Date(data.timestamp).toLocaleString() }}</div>
      </div>

      <div class="meta-right">
        <div class="meta-prices">
          <div class="price-item">
            <span class="price-label">Analysis Price</span>
            <span class="price-value">{{ fmt(data.current_price) }}</span>
          </div>
          <div class="price-item">
            <span class="price-label">Real-time Price</span>
            <span class="price-value" :class="{ 'price-up': realTimePrice > data.current_price, 'price-down': realTimePrice < data.current_price }">
              {{ fmt(realTimePrice) }}
            </span>
          </div>
        </div>

        <button
          v-if="data.analysis"
          class="save-btn"
          :class="`save-btn--${saveState}`"
          :disabled="saveState === 'saving'"
          @click="onSave"
        >
          <span v-if="saveState === 'idle'">💾 Save Snapshot</span>
          <span v-else-if="saveState === 'saving'">Saving…</span>
          <span v-else-if="saveState === 'saved'">✓ Saved</span>
          <span v-else-if="saveState === 'error'" :title="saveError">✗ Failed</span>
        </button>
      </div>
    </div>

    <!-- Trading Thesis -->
    <div v-if="analysis" class="card thesis-card">
      <div class="card-title">Trading Thesis</div>
      <div class="thesis-header">
        <span
          class="badge"
          :class="analysis.direction === 'long' ? 'badge--long' : 'badge--short'"
        >
          {{ analysis.direction === 'long' ? '▲ LONG' : '▼ SHORT' }}
        </span>
        <span
          class="badge"
          :class="`badge--${analysis.confidence_level}`"
        >
          {{ analysis.confidence_level }} confidence
        </span>
      </div>
      <p class="thesis-text">{{ analysis.trading_thesis }}</p>
      <p class="thesis-reason"><strong>Confidence reason:</strong> {{ analysis.confidence_reason }}</p>
    </div>

    <!-- No LLM analysis warning -->
    <div v-else class="card warning-card">
      <div class="card-title">⚠️ LLM Analysis Unavailable</div>
      <p class="warning-text">The LLM could not generate a trading analysis. Raw pipeline data is shown below.</p>
    </div>

    <!-- Entry / Exit Levels -->
    <div v-if="analysis" class="card">
      <div class="card-title">Entry / Exit Levels</div>
      <div class="levels-grid">
        <div class="level-block level--entry">
          <div class="level-label">Entry Zone</div>
          <div class="level-value">{{ fmt(analysis.entry_zone.low) }} — {{ fmt(analysis.entry_zone.high) }}</div>
        </div>
        <div class="level-block level--sl">
          <div class="level-label">Stop Loss</div>
          <div class="level-value">{{ fmt(analysis.stop_loss.price) }}</div>
          <div class="level-reason">{{ analysis.stop_loss.reason }}</div>
        </div>
      </div>
      <div class="tp-list">
        <div class="card-title" style="margin-top:12px">Take Profit Targets</div>
        <div v-for="tp in analysis.take_profit_targets" :key="tp.label" class="tp-row">
          <span class="tp-label badge badge--tag">{{ tp.label }}</span>
          <span class="tp-price">{{ fmt(tp.price) }}</span>
          <span class="tp-reason">{{ tp.reason }}</span>
        </div>
      </div>
    </div>

    <!-- Indicators -->
    <div class="card">
      <div class="card-title">Technical Indicators</div>
      <div class="indicator-grid">
        <div class="indicator-item">
          <span class="indicator-name">RSI (14)</span>
          <span class="indicator-val">{{ fmt(details.indicators.rsi_14) }}</span>
        </div>
        <div v-if="details.indicators.macd" class="indicator-item">
          <span class="indicator-name">MACD</span>
          <span class="indicator-val">
            {{ fmt(details.indicators.macd.value) }}
            <span class="indicator-sub">sig {{ fmt(details.indicators.macd.signal) }} · hist {{ fmt(details.indicators.macd.histogram) }}</span>
          </span>
        </div>
        <div v-if="details.indicators.bollinger" class="indicator-item">
          <span class="indicator-name">Bollinger</span>
          <span class="indicator-val">
            {{ fmt(details.indicators.bollinger.upper) }} / {{ fmt(details.indicators.bollinger.middle) }} / {{ fmt(details.indicators.bollinger.lower) }}
          </span>
        </div>
        <div class="indicator-item">
          <span class="indicator-name">SMA (20)</span>
          <span class="indicator-val">{{ fmt(details.indicators.sma_20) }}</span>
        </div>
        <div class="indicator-item">
          <span class="indicator-name">EMA (50)</span>
          <span class="indicator-val">{{ fmt(details.indicators.ema_50) }}</span>
        </div>
      </div>
    </div>

    <!-- SMC Data -->
    <div class="card">
      <div class="card-title">Smart Money Concepts</div>
      <div class="smc-section" v-if="details.smc.structure">
        <span class="smc-label">Structure</span>
        <span class="badge badge--tag">{{ details.smc.structure }}</span>
      </div>
      <div class="smc-section" v-if="details.smc.order_blocks.length">
        <span class="smc-label">Order Blocks</span>
        <div class="smc-items">
          <div v-for="(ob, i) in details.smc.order_blocks" :key="'ob'+i" class="smc-item">
            <span class="badge" :class="ob.type === 'bullish' ? 'badge--long' : 'badge--short'">{{ ob.type }}</span>
            <span>{{ fmt(ob.zone[0]) }} — {{ fmt(ob.zone[1]) }}</span>
            <span class="smc-tf badge badge--tag">{{ ob.timeframe }}</span>
          </div>
        </div>
      </div>
      <div class="smc-section" v-if="details.smc.fair_value_gaps.length">
        <span class="smc-label">Fair Value Gaps</span>
        <div class="smc-items">
          <div v-for="(fvg, i) in details.smc.fair_value_gaps" :key="'fvg'+i" class="smc-item">
            <span class="badge" :class="fvg.type === 'bullish' ? 'badge--long' : 'badge--short'">{{ fvg.type }}</span>
            <span>{{ fmt(fvg.zone[0]) }} — {{ fmt(fvg.zone[1]) }}</span>
            <span class="smc-tf badge badge--tag">{{ fvg.timeframe }}</span>
          </div>
        </div>
      </div>
      <div class="smc-section" v-if="details.smc.liquidity_sweeps.length">
        <span class="smc-label">Liquidity Sweeps</span>
        <div class="smc-tags">
          <span v-for="(ls, i) in details.smc.liquidity_sweeps" :key="'ls'+i" class="badge badge--tag">{{ ls }}</span>
        </div>
      </div>
      <p v-if="!details.smc.structure && !details.smc.order_blocks.length && !details.smc.fair_value_gaps.length && !details.smc.liquidity_sweeps.length" class="empty-text">
        No SMC signals detected
      </p>
    </div>

    <!-- Patterns -->
    <div class="card">
      <div class="card-title">Candlestick Patterns</div>
      <div v-if="details.patterns_detected.length" class="pattern-tags">
        <span v-for="p in details.patterns_detected" :key="p" class="badge badge--tag">{{ p }}</span>
      </div>
      <p v-else class="empty-text">No patterns detected</p>
    </div>

    <!-- Timeframes -->
    <div class="card">
      <div class="card-title">Timeframes Analyzed</div>
      <div class="tf-tags">
        <span v-for="tf in details.timeframes_analyzed" :key="tf" class="badge badge--tag">{{ tf }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
}

/* Meta header */
.result-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}

.meta-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-symbol {
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.meta-time {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.meta-prices {
  display: flex;
  gap: 24px;
}

/* Save button */
.save-btn {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 5px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.save-btn:hover:not(:disabled) {
  background: var(--accent-glow);
  border-color: var(--accent);
  color: var(--accent);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.save-btn--saved {
  border-color: var(--green);
  color: var(--green);
  background: rgba(34, 197, 94, 0.08);
}

.save-btn--error {
  border-color: var(--red);
  color: var(--red);
  background: rgba(239, 68, 68, 0.08);
}

.price-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.price-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.price-value {
  font-size: 1.1rem;
  font-weight: 700;
  font-family: var(--font-mono);
  transition: color 0.3s ease;
}

.price-up {
  color: var(--green);
}

.price-down {
  color: var(--red);
}

/* Thesis */
.thesis-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.thesis-text {
  font-size: 0.95rem;
  line-height: 1.7;
  margin-bottom: 8px;
}

.thesis-reason {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

/* Warning */
.warning-card {
  border-color: rgba(234, 179, 8, 0.3);
}

.warning-text {
  color: var(--yellow);
  font-size: 0.85rem;
}

/* Levels */
.levels-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.level-block {
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  background: var(--bg-input);
}

.level-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.level-value {
  font-size: 1.05rem;
  font-weight: 700;
  font-family: var(--font-mono);
}

.level--entry .level-value { color: var(--accent); }
.level--sl .level-value { color: var(--red); }

.level-reason {
  font-size: 0.72rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* TP targets */
.tp-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}

.tp-row:last-child {
  border-bottom: none;
}

.tp-price {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--green);
  min-width: 100px;
}

.tp-reason {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

/* Indicators */
.indicator-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.indicator-item:last-child {
  border-bottom: none;
}

.indicator-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.indicator-val {
  font-family: var(--font-mono);
  font-size: 0.88rem;
  font-weight: 500;
}

.indicator-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-left: 8px;
}

/* SMC */
.smc-section {
  margin-bottom: 14px;
}

.smc-section:last-child {
  margin-bottom: 0;
}

.smc-label {
  display: block;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.smc-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.smc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  font-family: var(--font-mono);
}

.smc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Patterns */
.pattern-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tf-tags {
  display: flex;
  gap: 8px;
}

.empty-text {
  font-size: 0.82rem;
  color: var(--text-muted);
  font-style: italic;
}
</style>
