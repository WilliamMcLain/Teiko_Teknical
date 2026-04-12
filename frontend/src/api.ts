import type { AnalysisRequest, AnalysisResponse, FilterOptions } from './types'

const BASE = '/api'

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const res = await fetch(`${BASE}/filters`)
  if (!res.ok) throw new Error('Failed to fetch filter options')
  return res.json()
}

export async function runAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
  const res = await fetch(`${BASE}/analyze`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(request),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Analysis failed')
  }
  return res.json()
}
