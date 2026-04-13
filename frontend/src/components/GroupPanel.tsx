import React from 'react'
import type { GroupFilter, FilterOptions, FilterOption } from '../types'
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

// The complete set of selectable values per field — source of truth for All toggle
export const ALL_VALUES: Record<string, string[]> = {
  conditions:   ['melanoma', 'carcinoma', 'cancer', 'healthy'],
  treatments:   ['miraclib', 'phauximab', 'drug', 'healthy'],
  sample_types: ['PBMC', 'WB'],
  sexes:        ['M', 'F'],
  responses:    ['yes', 'no'],
  time_points:  ['0', '7', '14'],
  projects:     ['prj1', 'prj2', 'prj3', 'prj1+prj2', 'prj2+prj3', 'prj1+prj3'],
}

function toggleOne(current: string[], val: string): string[] {
  return current.includes(val)
    ? current.filter(v => v !== val)
    : [...current, val]
}

const Chip: React.FC<{
  label:   string
  active:  boolean
  color:   string
  onClick: () => void
}> = ({ label, active, color, onClick }) => (
  <button
    onClick={onClick}
    style={{
      padding:      '4px 10px',
      borderRadius: '999px',
      border:       `1.5px solid ${active ? color : '#444'}`,
      background:   active ? color + '22' : 'transparent',
      color:        active ? color : '#888',
      fontSize:     '12px',
      cursor:       'pointer',
      transition:   'all 0.15s',
      fontFamily:   'DM Mono, monospace',
      fontWeight:   active ? 600 : 400,
    }}
  >
    {label}
  </button>
)

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ marginBottom: '12px' }}>
    <div style={{
      fontSize:      '10px',
      color:         '#555',
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
      marginBottom:  '6px',
      fontFamily:    'DM Mono, monospace',
    }}>
      {title}
    </div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
      {children}
    </div>
  </div>
)

export const GroupPanel: React.FC<Props> = ({
  group, color, filterOptions, onChange, onRemove, canRemove
}) => {
  const update = (patch: Partial<GroupFilter>) => onChange({ ...group, ...patch })

  function renderField(
    field: keyof GroupFilter,
    title: string,
    options: FilterOption[],
  ) {
    const selected  = group[field] as string[]
    const allVals   = ALL_VALUES[field as string]
    // All is active when every value in ALL_VALUES for this field is selected
    const allActive = allVals.every(v => selected.includes(v))

    return (
      <Section title={title}>
        <Chip
          label="All"
          color={color}
          active={allActive}
          onClick={() => update({ [field]: allActive ? [] : [...allVals] })}
        />
        {options.map(opt => {
          const val = String(opt.value)
          return (
            <Chip
              key={val}
              label={opt.label}
              color={color}
              active={selected.includes(val)}
              onClick={() => update({ [field]: toggleOne(selected, val) })}
            />
          )
        })}
      </Section>
    )
  }

  const allPopActive = CELL_POPULATIONS.every(p => group.populations.includes(p))

  return (
    <div style={{
      background:   '#111',
      border:       `1.5px solid ${color}44`,
      borderRadius: '12px',
      padding:      '16px',
      minWidth:     '260px',
      flex:         '1 1 260px',
    }}>

      {/* Header */}
      <div style={{
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'space-between',
        marginBottom:   '14px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
          <input
            value={group.label}
            onChange={e => update({ label: e.target.value })}
            style={{
              background:   'transparent',
              border:       'none',
              borderBottom: `1px solid ${color}66`,
              color:        '#fff',
              fontSize:     '14px',
              fontFamily:   'DM Serif Display, serif',
              fontWeight:   600,
              outline:      'none',
              width:        '120px',
            }}
          />
        </div>
        {canRemove && (
          <button
            onClick={onRemove}
            style={{ background: 'none', border: 'none', color: '#555', cursor: 'pointer', fontSize: '18px' }}
          >×</button>
        )}
      </div>

      {renderField('conditions',   'Condition',   filterOptions.conditions)}
      {renderField('treatments',   'Treatment',   filterOptions.treatments)}
      {renderField('sample_types', 'Sample Type', filterOptions.sample_types)}
      {renderField('sexes',        'Sex',         filterOptions.sexes)}
      {renderField('responses',    'Response',    filterOptions.responses)}
      {renderField('time_points',  'Time Point',  filterOptions.time_points)}
      {renderField('projects',     'Project',     filterOptions.projects)}

      {/* Cell Populations */}
      <Section title="Cell Populations">
        <Chip
          label="All"
          color={color}
          active={allPopActive}
          onClick={() => update({
            populations: allPopActive ? [] : [...CELL_POPULATIONS]
          })}
        />
        {CELL_POPULATIONS.map(pop => (
          <Chip
            key={pop}
            label={POPULATION_LABELS[pop]}
            color={color}
            active={group.populations.includes(pop)}
            onClick={() => update({ populations: toggleOne(group.populations, pop) })}
          />
        ))}
      </Section>
    </div>
  )
}