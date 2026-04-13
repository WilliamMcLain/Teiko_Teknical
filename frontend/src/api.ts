import type { AnalysisRequest, AnalysisResponse, FilterOptions } from './types'

const BASE = '/api'

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const res = await fetch(`${BASE}/filters`)
  if (!res.ok) throw new Error('Failed to fetch filter options')
  return res.json()
}

export async function runAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
  // Debug — log exact payload so we can see what's being sent
  console.log('REQUEST PAYLOAD:', JSON.stringify(request, null, 2))

  const res = await fetch(`${BASE}/analyze`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(request),
  })

  if (!res.ok) {
    // Try to parse JSON error detail from FastAPI
    // If the server returned HTML (500 crash), fall back to status text
    const contentType = res.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      const err = await res.json()
      // FastAPI wraps validation errors as { detail: [...] } or { detail: "string" }
      if (typeof err.detail === 'string') {
        throw new Error(err.detail)
      } else if (Array.isArray(err.detail)) {
        // Pydantic validation errors — extract the message
        const msg = err.detail.map((e: { msg: string }) => e.msg).join(', ')
        throw new Error(msg)
      }
      throw new Error('Analysis failed')
    } else {
      // Server returned non-JSON (e.g. 500 HTML page)
      throw new Error(`Server error (${res.status}): check the backend terminal for details`)
    }
  }

  return res.json()
}