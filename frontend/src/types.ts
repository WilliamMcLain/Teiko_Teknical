// =============================================================================
// API Types — mirrors backend Pydantic models
// =============================================================================

export const CELL_POPULATIONS = [
  "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"
] as const

export type Population = typeof CELL_POPULATIONS[number]

export const POPULATION_LABELS: Record<string, string> = {
  b_cell:     "B Cell",
  cd8_t_cell: "CD8 T Cell",
  cd4_t_cell: "CD4 T Cell",
  nk_cell:    "NK Cell",
  monocyte:   "Monocyte",
}

export const GROUP_COLORS = ["#2196F3", "#FF9800", "#4CAF50", "#F44336"]

export interface GroupFilter {
  label:        string
  conditions:   string[]
  treatments:   string[]
  sample_types: string[]
  sexes:        string[]
  responses:    string[]
  time_points:  (number | string)[]
  projects:     string[]
  populations:  string[]
}

export interface AnalysisRequest {
  groups: GroupFilter[]
}

// ── Response types ──────────────────────────────────────────────────────────

export interface CohortSummary {
  group:      string
  color:      string
  n_samples:  number
  n_subjects: number
}

export interface GroupHistData {
  label:  string
  color:  string
  values: number[]
}

export interface HistogramPopData {
  population: string
  groups:     GroupHistData[]
}

export interface GroupBoxData {
  label:  string
  color:  string
  values: number[]
  q1:     number
  median: number
  q3:     number
  iqr:    number
  min:    number
  max:    number
  mean:   number
}

export interface BoxplotPopData {
  population: string
  groups:     GroupBoxData[]
}

export interface StatRow {
  population:          string
  group_a:             string
  group_b:             string
  mean_a:              number
  mean_b:              number
  median_a:            number
  median_b:            number
  u_statistic:         number
  p_value_raw:         number
  p_value_corrected:   number | null
  bonferroni_applied:  boolean
  effect_size_rbc:     number
  significant:         boolean
}

export interface AnalysisResponse {
  cohort_summary:      CohortSummary[]
  histogram_data:      HistogramPopData[]
  boxplot_data:        BoxplotPopData[]
  stats:               StatRow[]
  bonferroni_applied:  boolean
  n_comparisons:       number | null
}

export interface FilterOption {
  value: string | number
  label: string
}

export interface FilterOptions {
  conditions:   FilterOption[]
  treatments:   FilterOption[]
  sample_types: FilterOption[]
  sexes:        FilterOption[]
  responses:    FilterOption[]
  time_points:  FilterOption[]
  projects:     FilterOption[]
  populations:  FilterOption[]
}
