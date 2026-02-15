/**
 * LazyBrother API client utility.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Run a trading analysis request.
 * @param {{ symbol: string, market: string, mode: string }} params
 * @returns {Promise<object>}
 */
export async function analyzeSymbol({ symbol, market, mode }) {
    const res = await fetch(`${BASE_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, market, mode }),
    })

    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const error = new Error(body.detail || `Request failed (${res.status})`)
        error.status = res.status
        throw error
    }

    return res.json()
}

/**
 * Check backend health.
 * @returns {Promise<object>}
 */
export async function healthCheck() {
    const res = await fetch(`${BASE_URL}/api/v1/health`)
    if (!res.ok) throw new Error('Backend unreachable')
    return res.json()
}
