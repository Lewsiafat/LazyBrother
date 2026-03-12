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
 * @param {{ symbol: string, mode: string, custom_prompt?: string, prompt_ids?: string[] }} params
 * @returns {Promise<object>}
 */
export async function analyzeSymbol({ symbol, mode, custom_prompt, prompt_ids }) {
    const res = await fetch(`${getBaseUrl()}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, mode, custom_prompt, prompt_ids }),
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

/**
 * Fetch available symbols from Binance.
 * @returns {Promise<string[]>}
 */
export async function fetchSymbols() {
    const res = await fetch(`${getBaseUrl()}/api/v1/symbols`)
    if (!res.ok) throw new Error('Failed to fetch symbols')
    return res.json()
}

/**
 * Prompt Management APIs
 */

export async function listPrompts() {
    const res = await fetch(`${getBaseUrl()}/api/v1/prompts`)
    if (!res.ok) throw new Error('Failed to load prompts')
    return res.json()
}

export async function createPrompt(data) {
    const res = await fetch(`${getBaseUrl()}/api/v1/prompts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error('Failed to create prompt')
    return res.json()
}

export async function updatePrompt(id, data) {
    const res = await fetch(`${getBaseUrl()}/api/v1/prompts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error('Failed to update prompt')
    return res.json()
}

export async function deletePrompt(id) {
    const res = await fetch(`${getBaseUrl()}/api/v1/prompts/${id}`, {
        method: 'DELETE'
    })
    if (!res.ok) throw new Error('Failed to delete prompt')
    return res.json()
}

export async function importPromptMarkdown(file) {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${getBaseUrl()}/api/v1/prompts/import`, {
        method: 'POST',
        body: formData
    })

    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to import markdown')
    }
    return res.json()
}
