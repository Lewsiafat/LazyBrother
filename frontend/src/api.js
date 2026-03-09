/**
 * LazyBrother API client utility.
 */

const DEFAULT_PORT = '8000'
const STORAGE_KEY = 'lazybrother_backend_port'

/**
 * Get the current backend base URL, reading port from localStorage.
 * Falls back to VITE_API_URL env var, then localhost:8000.
 */
export function getBaseUrl() {
    if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
    const port = localStorage.getItem(STORAGE_KEY) || DEFAULT_PORT
    return `http://localhost:${port}`
}

/**
 * Get/set the backend port stored in localStorage.
 */
export function getBackendPort() {
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_PORT
}

export function setBackendPort(port) {
    localStorage.setItem(STORAGE_KEY, String(port))
}

/**
 * Run a trading analysis request.
 * @param {{ symbol: string, market: string, mode: string }} params
 * @returns {Promise<object>}
 */
export async function analyzeSymbol({ symbol, market, mode }) {
    const res = await fetch(`${getBaseUrl()}/api/v1/analyze`, {
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
    const res = await fetch(`${getBaseUrl()}/api/v1/health`)
    if (!res.ok) throw new Error('Backend unreachable')
    return res.json()
}
