import React from 'react'
import type { AnalysisResponse } from '../types'
import { POPULATION_LABELS } from '../types'

interface Props {
  data: AnalysisResponse
}

const cell = (content: React.ReactNode, opts: { bold?: boolean; color?: string; mono?: boolean } = {}) => (
  <td style={{
    padding:    '8px 12px',
    borderBottom: '1px solid #1e1e1e',
    color:      opts.color ?? '#ccc',
    fontWeight: opts.bold ? 600 : 400,
    fontFamily: opts.mono ? 'DM Mono, monospace' : 'DM Sans, sans-serif',
    fontSize:   '12px',
    whiteSpace: 'nowrap',
  }}>
    {content}
  </td>
)

export const StatsTable: React.FC<Props> = ({ data }) => {
  const { stats, bonferroni_applied, n_comparisons, cohort_summary } = data

  return (
    <div style={{ marginTop: '32px' }}>

      {/* Cohort summary */}
      <h3 style={{ color: '#fff', fontFamily: 'DM Serif Display', fontSize: '18px', marginBottom: '12px', fontWeight: 400 }}>
        Cohort Summary
      </h3>
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '28px' }}>
        {cohort_summary.map(g => (
          <div key={g.group} style={{
            background:   '#111',
            border:       `1.5px solid ${g.color}44`,
            borderRadius: '10px',
            padding:      '12px 20px',
            minWidth:     '160px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '8px' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: g.color }} />
              <span style={{ color: '#fff', fontFamily: 'DM Serif Display', fontSize: '15px' }}>{g.group}</span>
            </div>
            <div style={{ color: '#aaa', fontSize: '12px', fontFamily: 'DM Mono' }}>
              <div>{g.n_samples.toLocaleString()} samples</div>
              <div>{g.n_subjects.toLocaleString()} subjects</div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats table */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '12px' }}>
        <h3 style={{ color: '#fff', fontFamily: 'DM Serif Display', fontSize: '18px', fontWeight: 400, margin: 0 }}>
          Statistical Results
        </h3>
        {bonferroni_applied && (
          <span style={{ fontSize: '11px', color: '#FF9800', fontFamily: 'DM Mono', background: '#FF980011', padding: '2px 8px', borderRadius: '999px', border: '1px solid #FF980033' }}>
            Bonferroni corrected · {n_comparisons} comparisons
          </span>
        )}
      </div>

      <div style={{ overflowX: 'auto', borderRadius: '10px', border: '1px solid #1e1e1e' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: '#0d0d0d' }}>
          <thead>
            <tr style={{ background: '#161616' }}>
              {[
                'Population', 'Group A', 'Group B',
                'Mean A (%)', 'Mean B (%)', 'Median A (%)', 'Median B (%)',
                'U Statistic', 'p (raw)', bonferroni_applied ? 'p (corrected)' : null,
                'Effect Size (RBC)', 'Significant'
              ].filter(Boolean).map(h => (
                <th key={h} style={{
                  padding:     '10px 12px',
                  textAlign:   'left',
                  color:       '#666',
                  fontSize:    '10px',
                  fontFamily:  'DM Mono, monospace',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  borderBottom: '1px solid #222',
                  whiteSpace:  'nowrap',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stats.map((row, i) => (
              <tr key={i} style={{ background: row.significant ? '#4CAF5008' : 'transparent' }}>
                {cell(POPULATION_LABELS[row.population] ?? row.population, { bold: true, color: '#fff' })}
                {cell(row.group_a)}
                {cell(row.group_b)}
                {cell(row.mean_a.toFixed(2) + '%', { mono: true })}
                {cell(row.mean_b.toFixed(2) + '%', { mono: true })}
                {cell(row.median_a.toFixed(2) + '%', { mono: true })}
                {cell(row.median_b.toFixed(2) + '%', { mono: true })}
                {cell(row.u_statistic.toLocaleString(), { mono: true })}
                {cell(row.p_value_raw.toFixed(6), { mono: true, color: row.p_value_raw < 0.05 ? '#4CAF50' : '#ccc' })}
                {bonferroni_applied && cell(
                  row.p_value_corrected?.toFixed(6) ?? '—',
                  { mono: true, color: (row.p_value_corrected ?? 1) < 0.05 ? '#4CAF50' : '#ccc' }
                )}
                {cell(row.effect_size_rbc.toFixed(4), { mono: true })}
                {cell(
                  row.significant ? '✓' : '—',
                  { bold: row.significant, color: row.significant ? '#4CAF50' : '#444' }
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p style={{ color: '#555', fontSize: '11px', fontFamily: 'DM Mono', marginTop: '10px' }}>
        Mann-Whitney U test (two-sided). Effect size = rank-biserial correlation. Significance threshold: p &lt; 0.05
        {bonferroni_applied ? ` after Bonferroni correction for ${n_comparisons} comparisons.` : '.'}
      </p>
    </div>
  )
}
