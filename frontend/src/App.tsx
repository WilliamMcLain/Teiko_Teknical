import React, { useEffect, useState } from 'react'
import { GroupPanel, ALL_VALUES } from './components/GroupPanel'
import { Charts } from './components/Charts'
import { StatsTable } from './components/StatsTable'
import { fetchFilterOptions, runAnalysis } from './api'
import type { GroupFilter, AnalysisResponse, FilterOptions } from './types'
import { GROUP_COLORS, CELL_POPULATIONS } from './types'

// Built directly from ALL_VALUES — single source of truth, guaranteed to match
const DEFAULT_GROUP = (index: number): GroupFilter => ({
  label:        `Group ${String.fromCharCode(65 + index)}`,
  conditions:   [...ALL_VALUES.conditions],
  treatments:   [...ALL_VALUES.treatments],
  sample_types: [...ALL_VALUES.sample_types],
  sexes:        [...ALL_VALUES.sexes],
  responses:    [...ALL_VALUES.responses],
  time_points:  [...ALL_VALUES.time_points],
  projects:     [...ALL_VALUES.projects],
  populations:  [...CELL_POPULATIONS],
})

export default function App() {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  const [groups, setGroups]               = useState<GroupFilter[]>([DEFAULT_GROUP(0)])
  const [result, setResult]               = useState<AnalysisResponse | null>(null)
  const [loading, setLoading]             = useState(false)
  const [error, setError]                 = useState<string | null>(null)
  const [chartType, setChartType]         = useState<'histogram' | 'boxplot'>('boxplot')

  useEffect(() => {
    fetchFilterOptions()
      .then(opts => {
        setFilterOptions(opts)
        // After filterOptions loads, reset groups so all chips are guaranteed active
        setGroups([DEFAULT_GROUP(0)])
      })
      .catch(() => setError('Could not connect to backend. Is the API running?'))
  }, [])

  const addGroup = () => {
    if (groups.length < 4) setGroups(g => [...g, DEFAULT_GROUP(g.length)])
  }

  const removeGroup = (i: number) => {
    setGroups(g => g.filter((_, idx) => idx !== i))
  }

  const updateGroup = (i: number, updated: GroupFilter) => {
    setGroups(g => g.map((grp, idx) => idx === i ? updated : grp))
  }

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await runAnalysis({ groups })
      setResult(res)
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight:   '100vh',
      background:  '#0a0a0a',
      color:       '#fff',
      fontFamily:  'DM Sans, sans-serif',
    }}>

      {/* Header */}
      <header style={{
        borderBottom: '1px solid #1a1a1a',
        padding:      '24px 40px',
        display:      'flex',
        alignItems:   'baseline',
        gap:          '16px',
      }}>
        <h1 style={{ fontFamily: 'DM Serif Display', fontSize: '28px', fontWeight: 400, margin: 0, color: '#fff' }}>
          Teiko Clinical Dashboard
        </h1>
        <span style={{ color: '#444', fontSize: '13px', fontFamily: 'DM Mono' }}>
          immune cell population analysis
        </span>
      </header>

      <main style={{ padding: '32px 40px', maxWidth: '1600px', margin: '0 auto' }}>

        {/* Group panels */}
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'flex-start', marginBottom: '24px' }}>
          {filterOptions && groups.map((group, i) => (
            <GroupPanel
              key={i}
              index={i}
              group={group}
              color={GROUP_COLORS[i]}
              filterOptions={filterOptions}
              onChange={updated => updateGroup(i, updated)}
              onRemove={() => removeGroup(i)}
              canRemove={groups.length > 1}
            />
          ))}

          {/* Add group button */}
          {groups.length < 4 && (
            <button
              onClick={addGroup}
              style={{
                minWidth:    '120px',
                height:      '60px',
                border:      '1.5px dashed #333',
                borderRadius: '12px',
                background:  'transparent',
                color:       '#555',
                fontSize:    '24px',
                cursor:      'pointer',
                alignSelf:   'center',
                transition:  'all 0.2s',
              }}
              onMouseEnter={e => { (e.target as HTMLElement).style.borderColor = '#666'; (e.target as HTMLElement).style.color = '#888' }}
              onMouseLeave={e => { (e.target as HTMLElement).style.borderColor = '#333'; (e.target as HTMLElement).style.color = '#555' }}
              title="Add group (max 4)"
            >
              +
            </button>
          )}
        </div>

        {/* Chart type toggle + Run button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
          <div style={{ display: 'flex', background: '#111', borderRadius: '8px', border: '1px solid #222', overflow: 'hidden' }}>
            {(['boxplot', 'histogram'] as const).map(type => (
              <button
                key={type}
                onClick={() => setChartType(type)}
                style={{
                  padding:    '8px 18px',
                  background: chartType === type ? '#1e1e1e' : 'transparent',
                  border:     'none',
                  color:      chartType === type ? '#fff' : '#555',
                  cursor:     'pointer',
                  fontSize:   '13px',
                  fontFamily: 'DM Sans',
                  fontWeight: chartType === type ? 600 : 400,
                  borderRight: type === 'boxplot' ? '1px solid #222' : 'none',
                }}
              >
                {type === 'boxplot' ? 'Box Plot' : 'Histogram'}
              </button>
            ))}
          </div>

          <button
            onClick={handleRun}
            disabled={loading}
            style={{
              padding:      '10px 28px',
              background:   loading ? '#1a1a1a' : '#2196F3',
              border:       'none',
              borderRadius: '8px',
              color:        loading ? '#555' : '#fff',
              fontSize:     '14px',
              fontWeight:   600,
              cursor:       loading ? 'not-allowed' : 'pointer',
              fontFamily:   'DM Sans',
              transition:   'all 0.2s',
              letterSpacing: '0.03em',
            }}
          >
            {loading ? 'Running…' : 'Run Analysis'}
          </button>

          {error && (
            <span style={{ color: '#F44336', fontSize: '13px', fontFamily: 'DM Mono' }}>
              ⚠ {error}
            </span>
          )}
        </div>

        {/* Results */}
        {result && (
          <div id="results">
            <div style={{
              background:   '#111',
              border:       '1px solid #1e1e1e',
              borderRadius: '14px',
              padding:      '24px',
              marginBottom: '24px',
            }}>
              <h2 style={{ fontFamily: 'DM Serif Display', fontSize: '20px', fontWeight: 400, margin: '0 0 20px 0', color: '#fff' }}>
                {chartType === 'boxplot' ? 'Box Plot' : 'Histogram'} — Relative Frequencies
              </h2>
              <Charts data={result} chartType={chartType} />
            </div>

            <div style={{
              background:   '#111',
              border:       '1px solid #1e1e1e',
              borderRadius: '14px',
              padding:      '24px',
            }}>
              <StatsTable data={result} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}