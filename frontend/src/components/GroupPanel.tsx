import React from 'react'
import type { GroupFilter, FilterOptions } from '../types'
import { CELL_POPULATIONS, POPULATION_LABELS } from '../types'

interface Props {
  index:         number
  group:         GroupFilter
  color:         string
  filterOptions: FilterOptions
  onChange:      (updated: GroupFilter) => void
  onRemove:      () => void
  canRemove:     boolean
}

// Helper — multi-select toggle
function toggle(arr: string[], val: string): string[] {
  return arr.includes(val) ? arr.filter(v => v !== val) : [...arr, val]
}

function toggleNum(arr: (number | string)[], val: number | string): (number | string)[] {
  return arr.includes(val) ? arr.filter(v => v !== val) : [...arr, val]
}

const Chip: React.FC<{
  label:    string
  active:   boolean
  color:    string
  onClick:  () => void
}> = ({ label, active, color, onClick }) => (
  <button
    onClick={onClick}
    style={{
      padding:         '4px 10px',
      borderRadius:    '999px',
      border:          `1.5px solid ${active ? color : '#444'}`,
      background:      active ? color + '22' : 'transparent',
      color:           active ? color : '#aaa',
      fontSize:        '12px',
      cursor:          'pointer',
      transition:      'all 0.15s',
      fontFamily:      'DM Mono, monospace',
      fontWeight:      active ? 600 : 400,
    }}
  >
    {label}
  </button>
)

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ marginBottom: '12px' }}>
    <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '6px', fontFamily: 'DM Mono, monospace' }}>
      {title}
    </div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
      {children}
    </div>
  </div>
)

export const GroupPanel: React.FC<Props> = ({ index, group, color, filterOptions, onChange, onRemove, canRemove }) => {
  const update = (patch: Partial<GroupFilter>) => onChange({ ...group, ...patch })

  return (
    <div style={{
      background:   '#111',
      border:       `1.5px solid ${color}44`,
      borderRadius: '12px',
      padding:      '16px',
      position:     'relative',
      minWidth:     '260px',
      flex:         '1 1 260px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
          <input
            value={group.label}
            onChange={e => update({ label: e.target.value })}
            style={{
              background:  'transparent',
              border:      'none',
              borderBottom: `1px solid ${color}66`,
              color:       '#fff',
              fontSize:    '14px',
              fontFamily:  'DM Serif Display, serif',
              fontWeight:  600,
              outline:     'none',
              width:       '120px',
            }}
          />
        </div>
        {canRemove && (
          <button onClick={onRemove} style={{ background: 'none', border: 'none', color: '#555', cursor: 'pointer', fontSize: '18px' }}>×</button>
        )}
      </div>

      {/* Condition */}
      <Section title="Condition">
        {filterOptions.conditions.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.conditions.includes(String(opt.value))}
            onClick={() => update({ conditions: toggle(group.conditions, String(opt.value)) })}
          />
        ))}
      </Section>

      {/* Treatment */}
      <Section title="Treatment">
        {filterOptions.treatments.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.treatments.includes(String(opt.value))}
            onClick={() => update({ treatments: toggle(group.treatments, String(opt.value)) })}
          />
        ))}
      </Section>

      {/* Sample Type */}
      <Section title="Sample Type">
        {filterOptions.sample_types.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.sample_types.includes(String(opt.value))}
            onClick={() => update({ sample_types: toggle(group.sample_types, String(opt.value)) })}
          />
        ))}
      </Section>

      {/* Sex */}
      <Section title="Sex">
        {filterOptions.sexes.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.sexes.includes(String(opt.value))}
            onClick={() => update({ sexes: toggle(group.sexes, String(opt.value)) })}
          />
        ))}
      </Section>

      {/* Response */}
      <Section title="Response">
        {filterOptions.responses.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.responses.includes(String(opt.value))}
            onClick={() => update({ responses: toggle(group.responses, String(opt.value)) })}
          />
        ))}
      </Section>

      {/* Time Point */}
      <Section title="Time Point">
        {filterOptions.time_points.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.time_points.includes(opt.value)}
            onClick={() => update({ time_points: toggleNum(group.time_points, opt.value) })}
          />
        ))}
      </Section>

      {/* Project */}
      <Section title="Project">
        {filterOptions.projects.map(opt => (
          <Chip key={opt.value} label={opt.label} color={color}
            active={group.projects.includes(String(opt.value))}
            onClick={() => update({ projects: toggle(group.projects, String(opt.value)) })}
          />
        ))}
      </Section>

      {/* Cell Populations */}
      <Section title="Cell Populations">
        {CELL_POPULATIONS.map(pop => (
          <Chip key={pop} label={POPULATION_LABELS[pop]} color={color}
            active={group.populations.includes(pop)}
            onClick={() => update({ populations: toggle(group.populations, pop) })}
          />
        ))}
      </Section>
    </div>
  )
}
